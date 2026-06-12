# -*- coding: utf-8 -*-
#
# Copyright (C) 2020-2026 Matthias Klumpp <matthias@tenstral.net>
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
from datetime import datetime, timezone

import numpy as np
import pytest

import edlio
from edlio import ureg
from edlio.dataset import EDLDataFile, EDLDataPart
from edlio.dataio.video import load_data as load_video_data

from . import source_root


def _can_decode_video(fname: str) -> bool:
    """Check whether the installed OpenCV can actually decode the given video."""
    import cv2 as cv

    cap = cv.VideoCapture(fname)
    try:
        ok, _ = cap.read()
        return bool(ok)
    finally:
        cap.release()


def test_load_intan_raw(samples_dir: str) -> None:
    test_coll = edlio.load(os.path.join(samples_dir, 'blink1'))
    assert isinstance(test_coll, edlio.EDLCollection)
    assert test_coll.collection_idname == 'blink1_21-02-08_608bc0ea'

    dset = test_coll.dataset_by_name('intan-signals')

    for intan in dset.read_data(include_nosync_time=True):
        times = intan.sync_times
        dig_chan_all = intan.digin_channels_raw
        assert dig_chan_all.any()

        ts_raw = intan._raw_data['timestamp']
        assert ts_raw.any()
        assert intan._timestamp_len == 1304640
        assert intan.digin_channels_raw[0].size == 1304640

        assert times[0] == 6.196 * ureg.ms
        assert intan._nosync_ts[0] == 6.196 * ureg.ms


def test_load_tsync_only(samples_dir: str) -> None:
    test_coll = edlio.load(os.path.join(samples_dir, 'blink1'))
    assert isinstance(test_coll, edlio.EDLCollection)
    assert test_coll.collection_idname == 'blink1_21-02-08_608bc0ea'

    dset = test_coll.group_by_name('videos').dataset_by_name('miniscope')

    tsync_data = [tsync for tsync in dset.read_aux_data('tsync')]
    assert len(tsync_data) == 1
    tsync = tsync_data[0]

    assert tsync.time_units == (ureg.dimensionless, ureg.millisecond)
    assert tsync.time_labels == ('frame-no', 'master-time')
    assert tsync.time_created == datetime.fromisoformat('2021-02-08 17:17:31').replace(
        tzinfo=timezone.utc
    )
    assert tsync.times.shape == (1287, 2)
    assert tsync.times.size == 2574


def test_load_crop1(samples_dir: str) -> None:
    from uuid import UUID

    test_coll = edlio.load(os.path.join(samples_dir, 'crop1'))
    assert isinstance(test_coll, edlio.EDLCollection)
    assert test_coll.collection_idname == 'crop1_26-06-12_37301b2c'
    assert test_coll.collection_id == UUID('019ebcd3-adfe-7f14-9723-692237301b2c')

    videos = test_coll.group_by_name('videos')
    for name, generator in (('raw-video', 'VR Raw'), ('cropped-video', 'VR Crop')):
        dset = videos.dataset_by_name(name)

        tsync_data = [tsync for tsync in dset.read_aux_data('tsync')]
        assert len(tsync_data) == 1
        tsync = tsync_data[0]

        assert tsync.generator_name == generator
        assert tsync.collection_id == test_coll.collection_id
        assert tsync.time_labels == ('frame-no', 'master-time')
        assert tsync.time_units == (ureg.dimensionless, ureg.microsecond)
        assert tsync.times.shape == (82, 2)


def test_load_crop1_video_frames(samples_dir: str) -> None:
    # The crop1 videos are AV1-encoded. The opencv-python wheels do not bundle a
    # software AV1 decoder yet (opencv/opencv-python#1209), so skip the frame
    # decoding checks when the installed OpenCV can not decode them.
    crop1_dir = os.path.join(samples_dir, 'crop1', 'videos')
    raw_mkv = os.path.join(crop1_dir, 'raw-video', '37301b2c-raw-video.mkv')
    if not _can_decode_video(raw_mkv):
        pytest.skip('Installed OpenCV has no working AV1 decoder (opencv/opencv-python#1209)')

    test_coll = edlio.load(os.path.join(samples_dir, 'crop1'))
    videos = test_coll.group_by_name('videos')

    # raw and cropped variants share frame count and timing, but the cropped
    # video has smaller frame dimensions (height, width, channels)
    for name, frame_shape in (('raw-video', (512, 512, 3)), ('cropped-video', (119, 128, 3))):
        dset = videos.dataset_by_name(name)
        tsync = next(dset.read_aux_data('tsync'))

        frames = list(dset.read_data())
        assert len(frames) == 82
        first = frames[0]
        assert first.mat.shape == frame_shape
        assert first.index == 0
        assert first.time == tsync.times[0, 1] * ureg.microsecond
        assert frames[-1].index == 81


def test_load_video_tsync_preserves_millisecond_timestamp_scale() -> None:
    dataset_path = os.path.join(
        source_root, 'tests', 'samples', 'blink1', 'videos', 'generic-camera'
    )

    aux_data = EDLDataFile(dataset_path, file_type='tsync')
    aux_data.parts.append(EDLDataPart('video_timestamps.tsync', 0))
    tsync = next(aux_data.read())

    frames = load_video_data([os.path.join(dataset_path, 'video.mkv')], [aux_data])
    frame = next(frames)
    expected_time_msec = tsync.times[0, 1]
    assert frame.time.to(tsync.time_units[1]).magnitude == expected_time_msec


def test_load_video_tsync_keeps_frame_index_unitless() -> None:
    dataset_path = os.path.join(
        source_root, 'tests', 'samples', 'blink1', 'videos', 'generic-camera'
    )

    aux_data = EDLDataFile(dataset_path, file_type='tsync')
    aux_data.parts.append(EDLDataPart('video_timestamps.tsync', 0))
    tsync = next(aux_data.read())

    frame = next(load_video_data([os.path.join(dataset_path, 'video.mkv')], [aux_data]))
    assert frame.index == tsync.times[0, 0]
    assert not hasattr(frame.index, 'units')


def test_load_json_csv(samples_dir: str) -> None:
    jcstore = edlio.load(os.path.join(samples_dir, 'jsoncsv1'))
    assert isinstance(jcstore, edlio.EDLCollection)
    assert jcstore.collection_idname == 'jsoncsv1_24-02-18_1779a25f'

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
    assert dfs[0].columns.tolist() == ['timestamp_msec', 'Int 1']
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
    assert dfs[0].columns.tolist() == ['timestamp_msec', 'Sine 1', 'Sine 2', 'Sine 3']
    assert dfs[0].shape == (4524, 4)

    # check reading a JSON string table
    dset = jcstore.dataset_by_name('table-json')
    assert dset.attributes == {'json_schema': 'pandas-split'}
    dfs = list(dset.read_data())
    assert len(dfs) == 1
    assert dfs[0].dtypes.array == [np.int64, np.dtype('O'), np.dtype('O')]
    assert dfs[0].columns.tolist() == ['Time', 'Tag', 'Value']
    assert dfs[0].shape == (5, 3)

    # check reading a CSV table as Pandas DataFrame
    dset = jcstore.dataset_by_name('table-csv')
    dfs = list(dset.read_data(as_dataframe=True))
    assert len(dfs) == 1
    assert dfs[0].dtypes.array == [np.int64, np.dtype('O'), np.dtype('O')]
    assert dfs[0].columns.tolist() == ['Time', 'Tag', 'Value']
    assert dfs[0].shape == (5, 3)

    # check reading a CSV table row-by-row
    dset = jcstore.dataset_by_name('table-csv')
    rows = list(dset.read_data())
    assert len(rows) == 6
    assert rows[0] == ['Time', 'Tag', 'Value']
    assert rows[-1] == ['20015', 'beta', 'eLcwGIFVu1A9NV']


def test_load_zarr(samples_dir: str) -> None:
    import zarr

    zcoll = edlio.load(os.path.join(samples_dir, 'zarrtest1'))
    assert isinstance(zcoll, edlio.EDLCollection)

    # 1D integer signal
    dset = zcoll.dataset_by_name('numbers_i32')
    stores = list(dset.read_data())
    assert len(stores) == 1
    root = stores[0]
    assert isinstance(root, zarr.Group)

    data = root['data']
    assert data.shape == (22476,)
    assert data.dtype == np.int32
    assert data.attrs['signal_names'] == ['Int Low']
    assert data.attrs['data_unit'] == 'au'

    timestamps = root['timestamps']
    assert timestamps.shape == (22476,)
    assert timestamps.dtype == np.uint64
    assert timestamps.attrs['time_unit'] == 'microseconds'

    # 2D multi-channel float signal
    dset = zcoll.dataset_by_name('sinesource')
    stores = list(dset.read_data())
    assert len(stores) == 1
    root = stores[0]
    assert isinstance(root, zarr.Group)

    data = root['data']
    assert data.shape == (22476, 3)
    assert data.dtype == np.float32
    assert data.attrs['signal_names'] == ['Low', 'High', 'Low+High']

    timestamps = root['timestamps']
    assert timestamps.shape == (22476,)
    assert timestamps.dtype == np.uint64
    assert timestamps.attrs['time_unit'] == 'microseconds'

    # 2D multi-channel integer signal with scale/offset metadata
    dset = zcoll.dataset_by_name('oe-acq-hs-a1')
    stores = list(dset.read_data())
    assert len(stores) == 1
    root = stores[0]
    assert isinstance(root, zarr.Group)

    data = root['data']
    assert data.shape == (168576, 8)
    assert data.dtype == np.uint16
    assert data.attrs['signal_names'] == ['CH{:02d}'.format(i) for i in range(1, 9)]
    assert data.attrs['data_unit'] == 'µV'
    assert data.attrs['data_scale'] == 0.19499999284744263
    assert data.attrs['data_offset'] == -6389.759765625

    timestamps = root['timestamps']
    assert timestamps.shape == (168576,)
    assert timestamps.dtype == np.uint64
    assert timestamps.attrs['time_unit'] == 'index'

    # 2D event signal
    dset = zcoll.dataset_by_name('oe-acq-ttl')
    stores = list(dset.read_data())
    assert len(stores) == 1
    root = stores[0]
    assert isinstance(root, zarr.Group)

    data = root['data']
    assert data.shape == (86, 2)
    assert data.dtype == np.uint32
    assert data.attrs['signal_names'] == ['line_id', 'value']
    assert data.attrs['data_unit'] == 'ttl'

    timestamps = root['timestamps']
    assert timestamps.shape == (86,)
    assert timestamps.dtype == np.uint64
    assert timestamps.attrs['time_unit'] == 'microseconds'
