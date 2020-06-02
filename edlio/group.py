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
import uuid
import toml
from .unit import EDLUnit, EDLError
from .dataset import EDLDataset


class EDLGroup(EDLUnit):
    '''
    An EDL Group
    '''

    def __init__(self):
        EDLUnit.__init__(self)
        self._children = []

    @property
    def children(self):
        return self._children

    @property
    def root_path(self) -> str:
        return self._root_path

    @root_path.setter
    def root_path(self, path: str) -> str:
        self._root_path = path
        for c in self._children:
            c.root_path = self.path

    @property
    def collection_id(self) -> uuid.UUID:
        return self._collection_id

    @collection_id.setter
    def collection_id(self, v: uuid.UUID):
        self._collection_id = v
        for c in self._children:
            c.collection_id = self._collection_id

    def change_name(self, new_name):
        EDLUnit.change_name(self, new_name)
        for c in self._children:
            c.root_path = self.path

    def add_child(self, child):
        if not isinstance(child, EDLUnit):
            raise ValueError('Can only have EDL units as children')
        child._parent = self
        child.root_path = self.path
        child.collection_id = self.collection_id
        self._children.append(child)

    @property
    def datasets(self):
        for child in self._children:
            if isinstance(child, EDLDataset):
                yield child

    @property
    def groups(self):
        for child in self._children:
            if isinstance(child, EDLGroup):
                yield child

    def group_by_name(self, name):
        for group in self.groups:
            if group.name == name:
                return group
        return None

    def dataset_by_name(self, name):
        for dset in self.datasets:
            if dset.name == name:
                return dset
        return None

    def save(self):
        mf = self._make_manifest_dict()
        self._save_metadata(mf, self.attributes)

    def load(self, path, mf={}):
        from .dataset import EDLDataset
        EDLUnit.load(self, path, mf)

        for d in os.listdir(self.path):
            unit_path = os.path.join(self.path, d)
            if not os.path.isdir(unit_path):
                continue
            mf_path = os.path.join(unit_path, 'manifest.toml')
            if not os.path.isfile(mf_path):
                continue

            with open(os.path.join(mf_path), 'r') as f:
                mf = toml.load(f)

            unit_type = mf.get('type')
            if unit_type == 'group':
                unit = EDLGroup()
            elif unit_type == 'dataset':
                unit = EDLDataset()
            else:
                raise EDLError('EDL unit type "{}" is unknown, data can not be loaded.'.format(unit_type))
            unit.load(unit_path, mf)
            self.add_child(unit)
