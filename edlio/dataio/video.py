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

from typing import Any, Optional, Sequence

import cv2 as cv
import numpy as np

from .. import ureg
from ..dataset import EDLDataFile
from .tsyncfile import TSyncFileMode


class Frame:
    mat: np.ndarray
    time: int
    index: int

    def __init__(self, mat, time, index):
        '''Create a new frame representation for a video file.

        Parameters
        ----------
        mat
            OpenCV matrix containing the image data.
        time
            Time as quantity (usually in milliseconds)
        index
            An optional frame index that increases monotonically.
        '''
        self.mat = mat
        self.time = time
        self.index = index


def load_data(part_paths, aux_data_entries: Sequence[EDLDataFile]):
    '''Entry point for automatic dataset loading.

    This function is used internally to load data from a video and expose
    it as stream of frames.
    '''
    sync_map: Optional[Any] = None

    aux_data: Optional[EDLDataFile] = None
    valid_timestamp_aux_keys = ['tsync', 'csv']
    for adf in aux_data_entries:
        for vtak in valid_timestamp_aux_keys:
            if vtak in adf.file_type or vtak in adf.media_type:
                aux_data = adf
                break
        if aux_data is not None:
            break

    if aux_data:
        if aux_data.file_type == 'csv' or aux_data.media_type == 'text/csv':
            sync_map = []
            for row in aux_data.read():
                if row[0] == 'frame':
                    # we have a table header, skip it
                    continue
                sync_map.append((int(row[0]), int(row[1])))
        elif aux_data.file_type == 'tsync':
            sync_map = np.empty([0, 2])
            for tsf in aux_data.read():
                if tsf.sync_mode != TSyncFileMode.CONTINUOUS:
                    raise Exception(
                        (
                            'Can not synchronize video timestamps using a '
                            'non-continuous tsync file.'
                        )
                    )
                if tsf.time_units[0] != ureg.dimensionless:
                    raise Exception(
                        'Unit of first time in tsync mapping has to be \'index\' for '
                        'video files.'
                    )
                if tsf.time_units[1] != ureg.msec:
                    raise Exception(
                        'We currently expect video timestamps to be in '
                        'milliseconds (unit was {}).'.format(tsf.time_units[1])
                    )
                sync_map = np.vstack((sync_map, tsf.times)) * ureg.msec
        else:
            raise Exception(
                'Unknown auxiliary data type ({}|{}) for video file.'.format(
                    aux_data.file_type, aux_data.media_type
                )
            )

    frame_index = 0
    for fname in part_paths:
        vc = cv.VideoCapture(fname)
        while True:
            ret, mat = vc.read()
            if not ret:
                break
            frame = (
                Frame(mat, sync_map[frame_index][1], sync_map[frame_index][0])
                if sync_map is not None
                else Frame(mat, -1, frame_index)
            )
            yield frame
            frame_index += 1
