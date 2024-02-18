# -*- coding: utf-8 -*-
#
# Copyright (C) 2020-2024 Matthias Klumpp <matthias@tenstral.net>
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

import os
from datetime import datetime

import numpy as np

import edlio
from edlio import ureg


def test_load_intan_raw(samples_dir):
    test_coll = edlio.load(os.path.join(samples_dir, 'blink1'))
    assert test_coll.collection_idname == 'blink1_21-02-08_a87011'

    dset = test_coll.dataset_by_name('intan-signals')

    for intan in dset.read_data(include_nosync_time=True):
        times = intan.sync_times
        dig_chan_all = intan._raw_data['DIGITAL-IN']
        assert dig_chan_all.any()

        ts_raw = intan._raw_data['timestamp']
        assert ts_raw.any()
        assert intan._timestamp_len == 1304640
        assert intan.digin_channels_raw[0].size == 1304640

        assert times[0] == 6.196 * ureg.ms
        assert intan._nosync_ts[0] == 6.196 * ureg.ms


def test_load_tsync_only(samples_dir):
    test_coll = edlio.load(os.path.join(samples_dir, 'blink1'))
    assert test_coll.collection_idname == 'blink1_21-02-08_a87011'

    dset = test_coll.group_by_name('videos').dataset_by_name('miniscope')

    tsync_data = [tsync for tsync in dset.read_aux_data('tsync')]
    assert len(tsync_data) == 1
    tsync = tsync_data[0]

    assert tsync.time_units == (ureg.dimensionless, ureg.millisecond)
    assert tsync.time_labels == ('frame-no', 'master-time')
    assert tsync.time_created == datetime.fromisoformat('2021-02-08 17:17:31')
    assert tsync.times.shape == (1287, 2)
    assert tsync.times.size == 2574


def test_load_json_csv(samples_dir):
    jcstore = edlio.load(os.path.join(samples_dir, 'jsoncsv1'))
    assert jcstore.collection_idname == 'jsoncsv1_24-02-18_336077'

    # check reading a pandas-extended JSON integer numbers set
    dset = jcstore.dataset_by_name('numbers-json')
    assert dset.attributes == {
        'json_data_unit': 'au',
        'json_schema': 'extended-pandas',
        'json_time_unit': 'milliseconds',
    }
    dfs = list(dset.read_data())
    assert len(dfs) == 1
    assert dfs[0].dtypes.array == [np.int64, np.int64]
    assert dfs[0].columns.array == ['timestamp_msec', 'Int 1']
    assert dfs[0].shape == (4524, 2)

    # check reading a pandas-compatible JSON float numbers set
    dset = jcstore.dataset_by_name('sines-json')
    assert dset.attributes == {
        'json_data_unit': 'au',
        'json_schema': 'pandas-split',
        'json_time_unit': 'milliseconds',
    }
    dfs = list(dset.read_data())
    assert len(dfs) == 1
    assert dfs[0].dtypes.array == [np.int64, np.float64, np.float64, np.float64]
    assert dfs[0].columns.array == ['timestamp_msec', 'Sine 1', 'Sine 2', 'Sine 3']
    assert dfs[0].shape == (4524, 4)

    # check reading a JSON string table
    dset = jcstore.dataset_by_name('table-json')
    assert dset.attributes == {'json_schema': 'pandas-split'}
    dfs = list(dset.read_data())
    assert len(dfs) == 1
    assert dfs[0].dtypes.array == [np.int64, np.dtype('O'), np.dtype('O')]
    assert dfs[0].columns.array == ['Time', 'Tag', 'Value']
    assert dfs[0].shape == (5, 3)

    # check reading a CSV table as Pandas DataFrame
    dset = jcstore.dataset_by_name('table-csv')
    dfs = list(dset.read_data(as_dataframe=True))
    assert len(dfs) == 1
    assert dfs[0].dtypes.array == [np.int64, np.dtype('O'), np.dtype('O')]
    assert dfs[0].columns.array == ['Time', 'Tag', 'Value']
    assert dfs[0].shape == (5, 3)

    # check reading a CSV table row-by-row
    dset = jcstore.dataset_by_name('table-csv')
    rows = list(dset.read_data())
    assert len(rows) == 6
    assert rows[0] == ['Time', 'Tag', 'Value']
    assert rows[-1] == ['20015', 'beta', 'eLcwGIFVu1A9NV']
