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

import os
from .unit import EDLUnit


class EDLDataPart:
    ''' Describes a part of a data file that has been split '''

    index: int = -1
    fname: str = None

    def __init__(self, fname: str):
        self.fname = fname
        self.index = -1


class EDLDataFile:
    ''' A data file, associated with a dataset '''

    class_name: str
    file_type: str
    media_type: str
    parts = []


class EDLDataset(EDLUnit):
    '''
    An EDL Dataset
    '''

    def __init__(self):
        EDLUnit.__init__(self)
