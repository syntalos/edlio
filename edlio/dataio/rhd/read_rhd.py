# -*- coding: utf-8 -*-
#
# Copyright (C) 2020 Matthias Klumpp <matthias@tenstral.net>
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
from numba import jit

from .read_rhd_raw import read_intan_data
from ..tsyncfile import TSyncFileMode, TSyncTimeUnit


@jit('int64 (double[:], double)', nopython=True, nogil=True)
def first_ge_index(vec, c):
    ''' Get the index of the first greater-equal number to `c`
    in ascending-sorted vector `vec` '''
    for i in range(len(vec)):
        if vec[i] >= c:
            return i
    return np.nan


@jit(nopython=True, nogil=True)
def make_synced_tsvec(data_len, sample_rate, sync_map, index_offset, init_sync_idx, init_offset_usec):
    ''' Create time vector, synchronizing all timepoints. '''
    offset_usec = init_offset_usec
    sync_idx = init_sync_idx

    tv_adj = np.zeros((data_len, 1), dtype=np.float64)
    for i in range(data_len):
        ts_msec = ((i + index_offset) / sample_rate) * 1000
        ts_usec = ts_msec * 1000

        ns_idx = first_ge_index(sync_map[:, 0][sync_idx:], ts_usec) + sync_idx
        if ns_idx > sync_idx:
            sync_idx = ns_idx
            offset_usec = sync_map[sync_idx][0] - sync_map[sync_idx][1]

        tv_adj[i] = ts_msec - (offset_usec / 1000)

    return tv_adj, offset_usec, sync_idx


@jit(nopython=True, nogil=True)
def make_nosync_tsvec(data_len, sample_rate, index_offset, start_offset_usec):
    ''' Create time vector taking only the start time into account. '''
    tv = np.zeros((data_len, 1), dtype=np.float64)
    for i in range(data_len):
        ts_msec = ((i + index_offset) / sample_rate) * 1000
        tv[i] = ts_msec - (start_offset_usec / 1000)

    return tv


def load_data(part_paths, aux_data, do_timesync=True, include_nosync_time=False):
    ''' Load Intan RHD signals data and apply time synchronization. '''

    start_offset_usec = 0
    sync_map = np.empty([0, 2])

    if aux_data:
        for tsf in aux_data.read():
            if tsf.sync_mode != TSyncFileMode.SYNCPOINTS:
                raise Exception('Can not synchronize RHD signal timestamps using a tsync file that is not in \'syncpoints\' mode.')
            if tsf.time_units != (TSyncTimeUnit.MICROSECONDS, TSyncTimeUnit.MICROSECONDS):
                raise Exception('For RHD signal synchronization, both timestamp units in tsync file must be microseconds. Found: {}'.format(tsf.time_units))
            sync_map = np.vstack((sync_map, tsf.times))
        start_offset_usec = sync_map[0][0] - sync_map[0][1]

    offset_usec = start_offset_usec
    sync_idx = 0
    data_pos_idx = 0
    has_sync_info = sync_map.size > 0
    log.info('Initial RHD time offset: {} µs ({})'.format(offset_usec, 'sync info found' if has_sync_info else 'no sync info'))
    if not do_timesync:
        log.info('RHD time synchronization disabled.')

    for fname in part_paths:
        idata = read_intan_data(fname)
        if not has_sync_info:
            yield idata
            continue

        time_for = 'amplifier'
        sample_rate = idata['frequency_parameters'].get('amplifier_sample_rate', -1)
        data_len = 0
        if sample_rate > 0:
            if 'amplifier_data' in idata:
                data_len = len(idata['amplifier_data'][0])
        else:
            time_for = 'dig_in'
            sample_rate = idata['frequency_parameters'].get('board_dig_in_sample_rate', -1)
            if 'board_dig_in_data' in idata:
                data_len = len(idata['board_dig_in_data'][0])
        if sample_rate <= 0:
            raise Exception('Unable to determine Intan sampling rate.')
        if data_len <= 0:
            raise Exception('Unable to determine Intan data length.')

        if do_timesync:
            tvec, offset_usec, sync_idx = make_synced_tsvec(data_len,
                                                            sample_rate,
                                                            sync_map,
                                                            data_pos_idx,
                                                            sync_idx,
                                                            offset_usec)
            if include_nosync_time:
                ns_tvec = make_nosync_tsvec(data_len,
                                            sample_rate,
                                            data_pos_idx,
                                            start_offset_usec)
                idata['times_nosync_{}_ms'.format(time_for)] = ns_tvec
        else:
            tvec = make_nosync_tsvec(data_len,
                                     sample_rate,
                                     data_pos_idx,
                                     start_offset_usec)
        data_pos_idx = data_pos_idx + data_len

        idata['times_{}_ms'.format(time_for)] = tvec
        yield idata
