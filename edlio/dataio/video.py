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

import typing as T
from collections.abc import Generator

import cv2 as cv
import numpy as np
from pint.facets.plain import PlainQuantity

from .. import ureg
from ..dataset import EDLDataFile
from .tsyncfile import TSyncFileMode


class Frame:
    mat: np.ndarray
    time: int | PlainQuantity[int]
    index: int

    def __init__(self, mat: np.ndarray, time: int | PlainQuantity[int], index: int):
        """Create a new frame representation for a video file.

        Parameters
        ----------
        mat
            OpenCV matrix containing the image data.
        time
            Time as quantity (usually in microseconds)
        index
            An optional frame index that increases monotonically.
        """
        self.mat = mat
        self.time = time
        self.index = index


def _read_video_aux_data(
    aux_data: EDLDataFile,
) -> Generator[tuple[int, PlainQuantity[int]], None, None]:
    if aux_data.file_type == 'csv' or aux_data.media_type == 'text/csv':
        for index, timestamp in aux_data.read():
            if index == 'frame':
                # we have a table header, skip it
                continue
            yield int(index), int(timestamp) * ureg.usec
        return

    if aux_data.file_type == 'tsync':
        for tsf in aux_data.read():
            if tsf.sync_mode != TSyncFileMode.CONTINUOUS:
                raise ValueError(
                    'Can not synchronize video timestamps using a non-continuous tsync file.'
                )
            if tsf.time_units[0] != ureg.dimensionless:
                raise ValueError(
                    'Unit of first time in tsync mapping has to be \'index\' for video files.'
                )
            if tsf.time_units[1] not in (ureg.msec, ureg.usec):
                raise ValueError(
                    'We currently expect video timestamps to be in microseconds or milliseconds (unit was {}).'.format(
                        tsf.time_units[1]
                    )
                )
            for index, timestamp in tsf.times:
                yield int(index), (int(timestamp) * tsf.time_units[1]).to(ureg.usec)

        return

    raise ValueError(
        'Unknown auxiliary data type ({}|{}) for video file.'.format(
            aux_data.file_type, aux_data.media_type
        )
    )


def load_data(
    part_paths: T.Iterable[str], aux_data_entries: T.Sequence[EDLDataFile]
) -> T.Iterator[Frame]:
    """Entry point for automatic dataset loading.

    This function is used internally to load data from a video and expose
    it as stream of frames.
    """
    aux_data: EDLDataFile | None = None
    valid_timestamp_aux_keys = ['tsync', 'csv']
    for adf in aux_data_entries:
        for vtak in valid_timestamp_aux_keys:
            if (adf.file_type and vtak in adf.file_type) or (
                adf.media_type and vtak in adf.media_type
            ):
                aux_data = adf
                break
        if aux_data is not None:
            break

    sync_map_gen = None
    if aux_data:
        sync_map_gen = _read_video_aux_data(aux_data)

    frame_index = 0
    for fname in part_paths:
        vc = cv.VideoCapture(fname)
        while True:
            ret, mat = vc.read()
            if not ret:
                break
            if sync_map_gen is None:
                frame = Frame(mat, time=-1, index=frame_index)
            else:
                index, time = next(sync_map_gen)
                frame = Frame(mat, time=time, index=index)
            yield frame
            frame_index += 1
