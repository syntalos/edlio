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

import logging as log
from typing import Optional

import numpy as np

try:
    from neo.rawio import IntanRawIO
    from neo.io.basefromrawio import BaseFromRaw
except ImportError as e:
    raise ImportError(
        'Unable to find the neo module. Can not read Intan electrophysiology data. {}'.format(
            str(e)
        )
    ) from e

from .. import ureg
from ..dataset import EDLDataFile
from .tsyncfile import TSyncFileMode


# pylint: disable=abstract-method
class SyncIntanReader(IntanRawIO, BaseFromRaw):
    '''Reader for Intan electrophysiology data.

    This class is the same as IntanIO from NEO, but additionally also provides
    synchronized timestamps in its :meth:`sync_times` property.
    '''

    _prefered_signal_group_mode = 'group-by-same-units'

    def __init__(self, intan_filename):
        IntanRawIO.__init__(self, filename=intan_filename)
        BaseFromRaw.__init__(self, intan_filename)
        self._sync_ts = None
        self._timestamp_len = 0
        self._digin_channels = None

    def _parse_header(self):
        IntanRawIO._parse_header(self)

    @property
    def has_adjusted_times(self) -> bool:
        '''Returns True if we have synchronized or otherwise adjusted time data.'''
        return self._sync_ts is not None

    @property
    def sync_times(self):
        '''Synchronized timestamps vector'''
        return self._sync_ts

    @property
    def digin_channels_raw(self):
        '''Obtain the raw data of digital input channels'''
        if self._digin_channels is not None:
            return self._digin_channels

        ts_len = self._timestamp_len
        digin_raw = self._raw_data['DIGITAL-IN'].flatten()
        if digin_raw.size > 0:
            # FIXME: We just assume 16 digital channels. This code should actually go into NEO
            # in a better form, instead of being hacked in here
            digin_chan_n = 16
            self._digin_channels = np.zeros((digin_chan_n, ts_len), dtype=bool)
            for i in range(0, digin_chan_n):
                self._digin_channels[i, :] = np.not_equal(np.bitwise_and(digin_raw, (1 << i)), 0)
        return self._digin_channels


def _make_nosync_tsvec(data_len, sample_rate, init_offset):
    '''Create time vector taking only the start time into account.'''
    tv = np.arange(0, data_len).astype(np.float64)
    tv = (tv / sample_rate).to(ureg.msec) - init_offset.to(ureg.msec)

    return tv


def _make_synced_tsvec(data_len, sample_rate, idx_intan, sync_map):
    '''
    Create time vector, synchronizing all timepoints.

    Syntalos monitors the timestamps coming from the external device and compares them to a
    prediction about what the actual timestamp based on its master clock should be.
    If the device timestamp is too large or to small compared to the prediction,
    Syntalos writes down the timepoint on its master clock next to the timestamp of the external
    device.
    Then it resets the prediction again based on the newly corrected time.

    To get continuous synchronized timestamps from the data provided by Syntalos, we just do a
    linear interpolation from one time point to the next.
    To do this quickly, we calculate the sampling index (based on the device time and device
    sampling rate) of each timepoint in :sync_map and move from one to the other.

    This works very well with accurate timing devices like Intan's RHD2000, CED, etc.
    It has *not* been tested with every device running its own clock.

    This specific function is written only for use with Intan (as it makes certain assumptions
    about the structure of the data).
    '''

    sync_len = sync_map.shape[0]
    if sync_len <= 2:
        # nothing to synchronize (we just have the initial offset and the end point),
        # just return the shifted vector
        log.debug(
            'Intan time sync map was too short for synchronization, '
            'returning timeshifted timestamp vector.'
        )
        init_offset = sync_map[0][0] - sync_map[0][1]
        return _make_nosync_tsvec(data_len, sample_rate, init_offset)

    tv_adj = np.zeros((data_len,), dtype=np.float64) * ureg.msec
    for i in range(sync_len - 1):
        # beginning of the 'frame' in master clock time
        m_start = sync_map[i, 1].to(ureg.msec)
        # end of the 'frame' in master clock time
        m_end = sync_map[i + 1, 1].to(ureg.msec)

        # beginning of the 'frame' in Intan sample indices
        d_start = idx_intan[i]
        # end of the 'frame' in Intan sample indices
        d_end = idx_intan[i + 1] + 1
        if d_end > data_len:
            log.error(
                'Intan sync index is bigger than the amount of recorded data ({} > {}). '
                'This means data may be missing or the time-sync files does not belong '
                'to this dataset'.format(d_end, data_len)
            )
            # try to do something semi-sensible, then abort as there is nothing we can do anymore
            d_end = data_len
            tv_adj[d_start:d_end] = np.linspace(m_start, m_end, d_end - d_start)
            break

        # linear interpolation between the beginning time point and the end time point
        # from the beginning sample index up to the end sample index
        tv_adj[d_start:d_end] = np.linspace(m_start, m_end, d_end - d_start)

        # last timepoint: just use the same slope and extrapolate to the end
        if i == (sync_len - 2):
            slope_part = (m_end - m_start) / (d_end - d_start)
            values_part = (np.arange(d_end, data_len) - d_end) * slope_part
            tv_adj[d_end : data_len + 1] = values_part + tv_adj[d_end - 1]
            break

    return tv_adj


def load_data(part_paths, aux_data_entries, do_timesync=True, include_nosync_time=False):
    '''Entry point for automatic dataset loading.

    This function is used internally to load Intan RHD signals data
    and apply time synchronization.
    '''

    start_offset = 0 * ureg.usec
    sync_map = np.empty([0, 2])

    aux_data: Optional[EDLDataFile] = None
    for adf in aux_data_entries:
        if 'tsync' in adf.file_type or 'tsync' in adf.media_type:
            aux_data = adf
            break

    if aux_data:
        tsf_count = 0
        for tsf in aux_data.read():
            if tsf.sync_mode != TSyncFileMode.SYNCPOINTS:
                raise Exception(
                    'Can not synchronize RHD signal timestamps using a tsync file '
                    'that is not in \'syncpoints\' mode.'
                )
            if tsf.time_units != (ureg.usec, ureg.usec):
                raise Exception(
                    'For RHD signal synchronization, both timestamp units in tsync '
                    'file must be microseconds. Found: {}'.format(tsf.time_units)
                )
            sync_map = np.vstack((sync_map, tsf.times)) * ureg.usec
            tsf_count += 1
        if tsf_count > 1:
            log.warning(
                'More than one tsync file found for Intan data '
                '- this is unusual and not a well-tested scenario.'
            )

        # the very first entry in the tsync file is the initial Intan to master-clock offset
        start_offset = sync_map[0][0] - sync_map[0][1]

    has_sync_info = sync_map.size > 0
    log.info(
        'Initial RHD time offset: {} µs ({})'.format(
            start_offset.magnitude, 'sync info found' if has_sync_info else 'no sync info'
        )
    )

    intan_readers = []
    for fname in part_paths:
        reader = SyncIntanReader(fname)
        if not has_sync_info:
            yield reader
            continue
        # data is lazily loaded from an mmap'ed file, so we can stash all readers here for now
        intan_readers.append(reader)

    # sanity checks and collect absolute data length of the whole recording
    recording_data_len = 0
    sample_rate = None
    for reader in intan_readers:
        if sample_rate is None:
            sample_rate = reader._max_sampling_rate * ureg.hertz
        else:
            if sample_rate != reader._max_sampling_rate * ureg.hertz:
                raise Exception(
                    'Samplig rate in Intan recording slice file differs from previous '
                    'files. The data may not belong to the same recording.'
                )
        reader._timestamp_len = reader._raw_data['timestamp'].size
        recording_data_len += reader._timestamp_len

    # convert to seconds and multiply with sampling rate to obtain sample indices
    intan_sync_idx = (sync_map[:, 0].to(ureg.seconds) * sample_rate).magnitude
    intan_sync_idx = intan_sync_idx.astype(np.int32)

    if do_timesync:
        tvec = _make_synced_tsvec(recording_data_len, sample_rate, intan_sync_idx, sync_map)
    if include_nosync_time or not do_timesync:
        tvec_noadj = _make_nosync_tsvec(recording_data_len, sample_rate, start_offset)
        if not do_timesync:
            tvec = tvec_noadj

    last_ts_idx = 0
    for reader in intan_readers:
        ts_len = reader._timestamp_len

        if include_nosync_time:
            reader._nosync_ts = tvec_noadj[last_ts_idx : last_ts_idx + ts_len]

        reader._sync_ts = tvec[last_ts_idx : last_ts_idx + ts_len]
        last_ts_idx += ts_len

        yield reader
