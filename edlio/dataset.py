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
import functools
from .unit import EDLUnit, EDLError
from .dataio import load_dataio_module, DATA_LOADERS


@functools.total_ordering
class EDLDataPart:
    ''' Describes a part of a data file that has been split '''

    index: int = -1
    fname: str = None

    def __init__(self, fname: str, index:int=-1):
        self.fname = fname
        self.index = index

    def __lt__(self, other):
        return self.index < other.index

    def __eq__(self, other):
        return self.index == other.index

    def __repr__(self):
        idx_str = '' if self.index < 0 else ', index=' + (str(self.index))
        return 'EDLDataPart(' + self.fname + idx_str + ')'


class EDLDataFile:
    ''' A data file, associated with a dataset '''

    parts = []

    def __init__(self, base_path, media_type:str=None, file_type:str=None):
        self._base_path = base_path
        self._media_type = media_type
        self._file_type = file_type
        self.parts = []

    @property
    def data_type(self):
        return (self._media_type, self._file_type)

    @property
    def media_type(self) -> str:
        return self._media_type

    @media_type.setter
    def media_type(self, mime: str) -> str:
        self._media_type = mime

    @property
    def file_type(self) -> str:
        return self._file_type

    @file_type.setter
    def file_type(self, ftype: str):
        self._file_type = ftype

    def __repr__(self):
        data_type = self._media_type if self._media_type else self._file_type
        return 'EDLDataFile(type=' + data_type + ', parts=' + str(self.parts) + ')'

    def part_paths(self):
        '''
        Return a generator for the path of each file-part, in their correct
        sorting order.
        '''
        for part in self.parts:
            yield os.path.join(self._base_path, part.fname)

    def read(self, aux_data=None):
        ''' Read all data parts in this set.

        This returns a generator which reads all the individual data parts in this data file.
        The data reader may take auxiliary data into account, if :aux_data is passed.
        '''

        dclass = self.media_type if self.media_type else self.file_type
        if not dclass:
            raise EDLError('This data file has no type association. EDL metadata was probably invalid, or this file does not exist.')
        if dclass.startswith('video/'):
            dclass = 'video'
        elif dclass.startswith('text/csv'):
            dclass = 'csv'

        if dclass not in DATA_LOADERS:
            raise EDLError('I do not know how to read data of type "{}".'.format(dclass))

        load_data = load_dataio_module(dclass)
        return load_data(self.part_paths(), aux_data)


class EDLDataset(EDLUnit):
    '''
    An EDL Dataset
    '''

    def __init__(self):
        EDLUnit.__init__(self)
        self._data = None
        self._aux_data = None

    @property
    def data(self) -> EDLDataFile:
        return self._data

    @data.setter
    def data(self, df: EDLDataFile):
        self._data = df

    @property
    def aux_data(self) -> EDLDataFile:
        return self._aux_data

    @aux_data.setter
    def aux_data(self, adf: EDLDataFile):
        self._aux_data = adf

    def load(self, path, mf={}):
        EDLUnit.load(self, path, mf)

        self._data = None
        self._aux_data = None
        if 'data' in mf:
            d = mf['data']
            df = EDLDataFile(self.path,
                             d.get('media_type'),
                             d.get('file_type'))
            for pi in d.get('parts', []):
                df.parts.append(EDLDataPart(pi['fname'], pi.get('index', -1)))
            if df.parts:
                df.parts.sort()
                self._data = df
        if 'data_aux' in mf:
            d = mf['data_aux']
            adf = EDLDataFile(self.path,
                              d.get('media_type'),
                              d.get('file_type'))
            for pi in d.get('parts', []):
                adf.parts.append(EDLDataPart(pi['fname'], pi.get('index', -1)))
            if adf.parts:
                adf.parts.sort()
                self._aux_data = adf

    def read_data(self):
        '''Read data from this dataset.

        Returns a generator to read data from this dataset by individual chunks, taking
        auxiliary data into account.
        '''
        if not self._data:
            return None
        return self._data.read(self._aux_data)
