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
import uuid
from typing import Any, Union, Optional, MutableMapping
from datetime import datetime

import tomlkit as toml

from .utils import sanitize_name

# version of the EDL specification
EDL_FORMAT_VERSION: str = '1'


class EDLError(Exception):
    '''Exception raised for errors in the input.

    Attributes:
        message -- explanation of the error
    '''

    def __init__(self, message):
        self.message = message
        super(EDLError, self).__init__(self.message)


class EDLUnit:
    '''
    Generic base class for all EDL unit types.
    '''

    def __init__(self, name=None):
        self._parent = None
        self._name = sanitize_name(name)
        self._collection_id = uuid.uuid4()
        self._root_path = ''
        self._authors = []
        self._attrs = {}
        self._format_version = EDL_FORMAT_VERSION
        self._generator_id = None
        self._unit_type = self._type_as_unittype()
        self._time_created = datetime.now().replace(microsecond=0)

    @property
    def parent(self):
        return self._parent

    @property
    def name(self):
        return self._name

    @property
    def unit_type(self):
        return self._unit_type

    @property
    def time_created(self) -> datetime:
        return self._time_created

    @time_created.setter
    def time_created(self, v: datetime):
        self._time_created = v

    @property
    def collection_id(self) -> uuid.UUID:
        return self._collection_id

    @collection_id.setter
    def collection_id(self, v: uuid.UUID):
        self._collection_id = v

    @property
    def path(self) -> str:
        if not self._root_path:
            return None
        return os.path.join(self._root_path, self._name)

    @property
    def root_path(self) -> str:
        return self._root_path

    @root_path.setter
    def root_path(self, path: str):
        self._root_path = path

    @property
    def authors(self):
        return self._authors

    @property
    def attributes(self) -> dict:
        return self._attrs

    @attributes.setter
    def attributes(self, v: dict):
        self._attrs = v

    def change_name(self, new_name: str):
        old_dir_path = self.path
        old_name = self.name

        # set new name, but sanitize it to be portable across many filesystems
        self._name = sanitize_name(new_name)

        if old_dir_path and os.path.exists(old_dir_path):
            try:
                os.rename(old_dir_path, self.path)
            except Exception as e:
                self._name = old_name
                raise ValueError('Unable to set new unit name: {}'.format(str(e))) from e

    def load(
        self, path: Union[str, os.PathLike[str]], mf: Optional[MutableMapping[str, Any]] = None
    ):
        '''
        Load an EDL unit from a path or path/data combination.

        Parameters
        ----------
        path
            Filesystem path of this dataset.
        mf
            Manifest file data as dictionary, if data from :path should not be used.
        '''
        if not os.path.isdir(path):
            raise EDLError(
                (
                    'Can not load unit from path "{}": Does not specify an ' 'existing directory'
                ).format(path)
            )
        if not mf:
            mf = {}

        path = str(path)
        self._name = os.path.basename(path.rstrip('/\\'))
        self._root_path = os.path.abspath(os.path.join(path, '..'))

        self._attrs = {}
        if not mf:
            with open(os.path.join(self.path, 'manifest.toml'), 'r', encoding='utf-8') as f:
                mf = toml.load(f)

        self._format_version = str(mf.get('format_version', 'unknown'))
        if self._format_version != EDL_FORMAT_VERSION:
            self._root_path = None
            self._name = None
            raise EDLError(
                (
                    'Can not load unit: Format version is unsupported '
                    '(was \'{}\', expected \'{}\').'
                ).format(self._format_version, EDL_FORMAT_VERSION)
            )

        unit_type = mf.get('type')
        if unit_type != self._unit_type:
            self._root_path = None
            self._name = None
            msg = 'EDL Unit type of "{}" can not be loaded by this "{}" object.'.format(
                unit_type, self._unit_type
            )
            raise EDLError(msg)

        if os.path.isfile(os.path.join(self.path, 'attributes.toml')):
            with open(os.path.join(self.path, 'attributes.toml'), 'r', encoding='utf-8') as f:
                self._attrs = toml.load(f)

        self._time_created = mf['time_created']
        if 'collection_id' in mf:
            self._collection_id = uuid.UUID(str(mf['collection_id']))
        if 'generator' in mf:
            self._generator_id = mf['generator']
        if 'authors' in mf:
            self._authors = mf['authors']

    def _type_as_unittype(self):
        from .group import EDLGroup
        from .dataset import EDLDataset
        from .collection import EDLCollection

        if isinstance(self, EDLCollection):
            return 'collection'
        if isinstance(self, EDLGroup):
            return 'group'
        if isinstance(self, EDLDataset):
            return 'dataset'
        raise NotImplementedError('An abstract EDL object does not have a defined type.')

    def _make_manifest_dict(self):
        if not self._time_created:
            # set default creation time, with second-resolution (milliseconds are stripped)
            self._time_created = datetime.now().replace(microsecond=0)

        doc = {}
        doc['format_version'] = self._format_version
        doc['type'] = self._type_as_unittype()

        if self.collection_id:
            doc['collection_id'] = str(self.collection_id)

        doc['time_created'] = self._time_created

        if self._generator_id:
            doc['generator'] = self._generator_id

        if self._authors:
            doc['authors'] = self._authors

        return doc

    def _save_metadata(self, manifest, attributes):
        if not self.path:
            raise EDLError('No path is set for this EDL unit')
        os.makedirs(self.path, exist_ok=True)

        with open(os.path.join(self.path, 'manifest.toml'), 'w', encoding='utf-8') as f:
            toml.dump(manifest, f)

        if attributes:
            with open(os.path.join(self.path, 'attributes.toml'), 'w', encoding='utf-8') as f:
                toml.dump(attributes, f)
