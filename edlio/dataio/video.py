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
import cv2 as cv

class Frame:
    mat: np.ndarray
    time: int
    index: int

    def __init__(self, mat, time, index):
        self.mat = mat
        self.time = time
        self.index = index

def load_data(part_paths, aux_data):
    ''' Entry point for automatic dataset loading '''
    adata = []
    if aux_data:
        header = True
        for row in aux_data.read():
            if header:
                header = False
                continue
            adata.append((int(row[0]), int(row[1])))

    frame_index = 0
    for fname in part_paths:
        vc = cv.VideoCapture(fname)
        while True:
            ret, mat = vc.read()
            if not ret:
                break
            frame = Frame(mat, adata[frame_index][1], adata[frame_index][0]) if adata else Frame(mat, -1, frame_index)
            yield frame
            frame_index += 1
