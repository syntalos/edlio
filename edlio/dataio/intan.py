# -*- coding: utf-8 -*-
#
# Copyright (C) 2020-2021 Matthias Klumpp <matthias@tenstral.net>
#
# Licensed under the GNU Lesser General Public License Version 3
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as published by
# the Free Software Foundation, either version 3 of the license, or
# (at your option) any later version.
#
# This software is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with this software.  If not, see <http://www.gnu.org/licenses/>.

import numpy as np
import logging as log

try:
    from neo.rawio import IntanRawIO
    from neo.io.basefromrawio import BaseFromRaw
except ImportError as e:
    raise ImportError('Unable to find the neo module. Can not read Intan electrophysiology data. {}'.format(str(e)))

from .tsyncfile import TSyncFileMode
from .. import ureg


class SyncIntanReader(IntanRawIO, BaseFromRaw):
    __doc__ = IntanRawIO.__doc__
    _prefered_signal_group_mode = 'group-by-same-units'

    def __init__(self, intan_filename):
        IntanRawIO.__init__(self, filename=intan_filename)
        BaseFromRaw.__init__(self, intan_filename)
        self._sync_ts = None

    def _parse_header(self):
        IntanRawIO._parse_header(self)

    @property
    def has_adjusted_times(self) -> bool:
        ''' Returns True if we have synchronized or otherwise adjusted time data. '''
        return self._sync_ts is not None

    @property
    def sync_times(self):
        return self._sync_ts


def make_nosync_tsvec(data_len, sample_rate, index_offset, start_offset):
    ''' Create time vector taking only the start time into account. '''
    tv = np.arange(0, data_len).astype(np.float64)
    tv = ((tv + index_offset) / sample_rate).to(ureg.msec) - start_offset.to(ureg.msec)
    return tv


def make_synced_tsvec(data_len, sample_rate, sync_map, index_offset, init_sync_idx, init_offset):
    '''
    Create time vector, synchronizing all timepoints.

    Syntalos monitors the timestamps coming from the external device and compares them to a prediction
    about what the actual timestamp based on its master clock should be.
    If the device timestamp is too large or to small compared to the prediction,
    Syntalos writes down the timepoint on its master clock next to the timestamp of the external device.
    Then it resets the prediction again based on the newly corrected time.

    To get continuous synchronized timestamps from the data provided by Syntalos, we just do a linear interpolation
    from one time point to the next.
    To do this quickly, we calculate the sampling index (based on the device time and device sampling rate)
    of each timepoint in :sync_map and move from one to the other.

    This works very well with accurate timing devices like Intan's RHD2000, CED, etc.
    It has *not* been tested with every device running its own clock.

    This specific function is written only for use with Intan (as it makes certain assumptions about the
    structure of the data).
    '''

    tv_adj = np.zeros((data_len, ), dtype=np.float64) * ureg.msec
    init_offset = init_offset.to(ureg.msec)

    # convert to seconds and multiply with sampling rate to obtain sample indices
    idx_intan = (sync_map[:, 0].to(ureg.seconds).magnitude * sample_rate.magnitude) + index_offset
    idx_intan = idx_intan.astype(np.int32)

    sync_len = sync_map.shape[0]
    if (init_sync_idx + 1) >= sync_len:
        # nothing to synchronize, just return the shifted vector
        tv_adj = make_nosync_tsvec(data_len, sample_rate, index_offset, init_offset)
        return tv_adj, sync_len

    for i in range(init_sync_idx, sync_len - 1):
        # beginning of the 'frame' in master clock time
        m_start = sync_map[i, 1].to(ureg.msec)
        # end of the 'frame' in master clock time
        m_end = sync_map[i + 1, 1].to(ureg.msec)

        # beginning of the 'frame' in Intan sample indices
        d_start = idx_intan[i]
        # end of the 'frame' in Intan sample indices
        d_end = idx_intan[i + 1] + 1
        if d_end > data_len:
            d_end = data_len

        # obtain time-vector slice indices
        t_start = d_start - index_offset
        t_end = d_end - index_offset

        # linear interpolation between the beginning time point and the end time point
        # from the beginning sample index up to the end sample index
        tv_adj[t_start:t_end] = np.linspace(m_start, m_end, d_end - d_start) - init_offset

        # initial timepoint: just use the same slope and extrapolate to the beginning
        if i == 0:
            slope_part = (m_end - m_start) / (d_end - d_start)
            values_part = np.arange(0, d_start + 1) * slope_part
            tv_adj[0:t_start + 1] = (values_part - values_part[-1] + tv_adj[d_start]) - init_offset

        # last timepoint: just use the same slope and extrapolate to the end
        if i == (sync_len - 2):
            slope_part = (m_end - m_start) / (d_end - d_start)
            values_part = (np.arange(d_end, data_len) - d_end) * slope_part
            tv_adj[t_end:data_len + 1] = (values_part + tv_adj[d_end - 1]) - init_offset

        if d_end == data_len:
            break

    return tv_adj, i


def load_data(part_paths, aux_data, do_timesync=True, include_nosync_time=False):
    ''' Load Intan RHD signals data and apply time synchronization. '''

    start_offset_usec = 0
    sync_map = np.empty([0, 2])

    if aux_data:
        tsf_count = 0
        for tsf in aux_data.read():
            if tsf.sync_mode != TSyncFileMode.SYNCPOINTS:
                raise Exception('Can not synchronize RHD signal timestamps using a tsync file that is ' +
                                'not in \'syncpoints\' mode.')
            if tsf.time_units != (ureg.usec, ureg.usec):
                raise Exception('For RHD signal synchronization, both timestamp units in tsync file must be ' +
                                'microseconds. Found: {}'.format(tsf.time_units))
            sync_map = np.vstack((sync_map, tsf.times)) * ureg.usec
            tsf_count += 1
        if tsf_count > 1:
            log.warning('More than one tsync file found for Intan data ' +
                        '- this is unusual and not a well-tested scenario.')

        # the very first entry in the tsync file is the initial Intan to master-clock offset
        start_offset = sync_map[0][0] - sync_map[0][1]

    sync_idx = 0
    data_pos_idx = 0
    has_sync_info = sync_map.size > 0
    log.info('Initial RHD time offset: {} µs ({})'
             .format(start_offset.magnitude, 'sync info found' if has_sync_info else 'no sync info'))

    # skip initial base offset sync point
    sync_map = sync_map[1:, :]

    for fname in part_paths:
        reader = SyncIntanReader(fname)
        if not has_sync_info:
            yield reader
            continue

        reader._sync_map = sync_map

        sample_rate = reader._max_sampling_rate * ureg.hertz
        data_len = reader._raw_data['timestamp'].shape[0]

        if do_timesync:
            tvec, sync_idx = make_synced_tsvec(data_len,
                                               sample_rate,
                                               sync_map,
                                               data_pos_idx,
                                               sync_idx,
                                               start_offset)
        else:
            tvec = make_nosync_tsvec(data_len,
                                     sample_rate,
                                     data_pos_idx,
                                     start_offset_usec)
        reader._sync_ts = tvec

        if include_nosync_time:
            reader._nosync_ts = make_nosync_tsvec(data_len,
                                                  sample_rate,
                                                  data_pos_idx,
                                                  start_offset_usec)

        data_pos_idx = data_pos_idx + data_len
        yield reader
