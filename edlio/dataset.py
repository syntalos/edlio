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

from __future__ import annotations

import os
import functools
from typing import Any, Union, Optional, Sequence, MutableMapping

from .unit import EDLUnit, EDLError
from .dataio import DATA_LOADERS, load_dataio_module


@functools.total_ordering
class EDLDataPart:
    '''Describes a part of a data file that has been split'''

    index: int = -1
    fname: str = None

    def __init__(self, fname: str, index: int = -1):
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
    '''A data file, associated with a dataset'''

    parts: list[EDLDataPart] = []

    def __init__(self, base_path, media_type: str = None, file_type: str = None):
        self._base_path = base_path
        self._media_type = media_type
        self._file_type = file_type
        self._summary: Optional[str] = None
        self.parts = []

    @property
    def data_type(self):
        return (self._media_type, self._file_type)

    @property
    def media_type(self) -> Optional[str]:
        '''The media (MIME) type of this data.'''
        return self._media_type

    @media_type.setter
    def media_type(self, mime: Optional[str]):
        self._media_type = mime

    @property
    def file_type(self) -> Optional[str]:
        '''´ The filetype, in case no media type was available.'''
        return self._file_type

    @file_type.setter
    def file_type(self, ftype: Optional[str]):
        self._file_type = ftype

    @property
    def summary(self) -> Optional[str]:
        '''A human-readable summary of what this data is about.'''
        return self._summary

    @summary.setter
    def summary(self, text: Optional[str]):
        '''Set the summary text'''
        self._summary = text

    def __repr__(self):
        data_type = self._media_type if self._media_type else self._file_type
        return (
            'EDLDataFile(type='
            + data_type
            + ', parts='
            + str(self.parts)
            + ', summary='
            + str(self.summary)
            + ')'
        )

    def part_paths(self):
        '''
        Return a generator for the path of each file-part, in their correct
        sorting order.
        '''
        for part in self.parts:
            yield os.path.join(self._base_path, part.fname)

    def new_part(self, fname: str, index: int = -1, *, allow_exists=False):
        if not fname:
            raise ValueError('File name is not valid.')
        _, fext = os.path.splitext(fname)
        if fext and fext.startswith('.'):
            fext = fext[1:]
        if not self._file_type:
            self._file_type = fext
        elif self._file_type != fext:
            raise ValueError(
                'New part does not have the right extension for this data: {}'.format(
                    self._file_type
                )
            )
        for ep in self.parts:
            if ep.fname == fname:
                if allow_exists:
                    return ep, os.path.join(self._base_path, ep.fname)
                raise ValueError('A file part with name "{}" already exists.'.format(fname))
        part = EDLDataPart(fname, index)
        self.parts.append(part)
        return part, os.path.join(self._base_path, part.fname)

    def read(self, aux_data_entries: Optional[Sequence[EDLDataFile]] = None, **kwargs):
        '''Read all data parts in this set.

        This returns a generator which reads all the individual data parts in this data file.
        The data reader may take auxiliary data into account, if :aux_data is passed.
        '''
        if not aux_data_entries:
            aux_data_entries = []

        dclass = self.media_type if self.media_type else self.file_type
        if not dclass:
            raise EDLError(
                (
                    'This data file has no type association. EDL metadata was '
                    'probably invalid, or this file does not exist.'
                )
            )
        if dclass.startswith('video/'):
            dclass = 'video'
        elif dclass.startswith('text/csv'):
            dclass = 'csv'

        if dclass not in DATA_LOADERS:
            raise EDLError('I do not know how to read data of type "{}".'.format(dclass))

        load_data = load_dataio_module(dclass)
        return load_data(self.part_paths(), aux_data_entries, **kwargs)


class EDLDataset(EDLUnit):
    '''
    An EDL Dataset
    '''

    def __init__(self, name=None):
        '''
        Create a new EDL dataset.

        If the dataset has no name and path set, it can not be saved
        to disk.

        Parameters
        ----------
        name
            Name of this dataset, or None
        '''
        EDLUnit.__init__(self, name)
        self._data = EDLDataFile(self.path)
        self._aux_data = []

    @property
    def data(self) -> EDLDataFile:
        return self._data

    @data.setter
    def data(self, df: EDLDataFile):
        self._data = df

    @property
    def aux_data(self) -> list[EDLDataFile]:
        return self._aux_data

    def add_aux_data(self, adf: EDLDataFile):
        self._aux_data.append(adf)

    def _parse_data_md(self, d: dict[str, Any]):
        df = EDLDataFile(self.path, d.get('media_type'), d.get('file_type'))
        df.summary = d.get('summary')
        for pi in d.get('parts', []):
            df.parts.append(EDLDataPart(pi['fname'], pi.get('index', -1)))
        if df.parts:
            df.parts.sort()
        return df

    def load(
        self, path: Union[str, os.PathLike[str]], mf: Optional[MutableMapping[str, Any]] = None
    ):
        '''
        Load an EDL dataset from a path.

        Parameters
        ----------
        path
            Filesystem path of this dataset.
        mf
            Manifest file data as dictionary, if data from :path should not be used.
        '''
        if not mf:
            mf = {}
        EDLUnit.load(self, path, mf)

        self._data = EDLDataFile(self.path)
        self._aux_data = []
        if 'data' in mf:
            self._data = self._parse_data_md(mf['data'])
        if 'data_aux' in mf:
            daux_raw = mf['data_aux']
            if isinstance(daux_raw, dict):
                self._aux_data.append(self._parse_data_md(daux_raw))
            else:
                for adf_raw in daux_raw:
                    self._aux_data.append(self._parse_data_md(adf_raw))

    def _serialize_data_md(self, df):
        d = {}
        if not df.parts:
            return {}
        if self._data.media_type:
            d['media_type'] = df.media_type
        elif self._data.file_type:
            d['file_type'] = df.file_type
        if df.summary:
            d['summary'] = df.summary
        d['parts'] = []
        for part in df.parts:
            pd = {'fname': part.fname}
            if part.index >= 0:
                pd['index'] = part.index
            d['parts'].append(pd)
        return d

    def save(self):
        '''Save dataset changes to their current location on disk.'''
        if not self.path:
            raise ValueError('No path set for EDL group "{}"'.format(self.name))
        os.makedirs(self.path, exist_ok=True)

        mf = self._make_manifest_dict()
        mf['data'] = self._serialize_data_md(self._data)
        if self._aux_data:
            adf_list = []
            for adf in self._aux_data:
                adf_list.append(self._serialize_data_md(adf))
            mf['data_aux'] = adf_list

        self._save_metadata(mf, self.attributes)

    def read_data(self, **kwargs):
        '''Read data from this dataset.

        Returns a generator to read data from this dataset by individual chunks, taking
        auxiliary data into account.
        '''
        if not self._data:
            return None
        return self._data.read(self._aux_data, **kwargs)

    def read_aux_data(self, key: Optional[str] = None) -> Optional[Any]:
        '''
        Read auxiliary data from this dataset.

        Parameters
        ----------
        key
            Identifier key for the auxiliary dataset to load.
            Will look for a substring match in file_type/media_type
            properties of the data first, then look for a summary text match
            to determine which data was requested. If not set, the first dataset
            is loaded.
        Returns
        -------
        The data, or None in case no aux-data or aux-data entry was found.
        '''
        if not self._aux_data:
            return None
        if not key:
            return self._aux_data[0].read()
        for adf in self._aux_data:
            if key in adf.file_type or key in adf.media_type:
                return adf.read()
        for adf in self._aux_data:
            if key in adf.summary:
                return adf.read()
        return None
