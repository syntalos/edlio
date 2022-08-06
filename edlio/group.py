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

import tomlkit as toml

from .unit import EDLUnit, EDLError
from .dataset import EDLDataset


class EDLGroup(EDLUnit):
    '''
    An EDL Group
    '''

    def __init__(self, name: str = None):
        '''
        Create a new EDL group.

        If the group has no name and path set, it can not be saved
        to disk.

        Parameters
        ----------
        name
            Name of this group, or None
        '''
        EDLUnit.__init__(self, name)
        self._children: list[EDLUnit] = []

    @property
    def children(self):
        return self._children

    @property
    def root_path(self) -> str:
        return self._root_path

    @root_path.setter
    def root_path(self, path: str):
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

    def add_child(self, child: EDLUnit):
        if not isinstance(child, EDLUnit):
            raise ValueError('Can only have EDL units as children.')
        if not child.name:
            raise ValueError('Child unit must have a name.')
        old_path = None
        if child.root_path:
            old_path = child.path
        child._parent = self
        child.root_path = self.path
        child.collection_id = self.collection_id

        if old_path and os.path.isdir(old_path):
            os.rename(old_path, child.path)
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

    def group_by_name(self, name, *, create=False):
        for group in self.groups:
            if group.name == name:
                return group
        group = None
        if create:
            group = EDLGroup(name)
            self.add_child(group)
            group.save()
        return group

    def dataset_by_name(self, name, *, create=False):
        for dset in self.datasets:
            if dset.name == name:
                return dset
        dset = None
        if create:
            dset = EDLDataset(name)
            self.add_child(dset)
            dset.save()
        return dset

    def save(self):
        if not self.path:
            raise ValueError('No path set for EDL group "{}"'.format(self.name))
        os.makedirs(self.path, exist_ok=True)

        mf = self._make_manifest_dict()
        self._save_metadata(mf, self.attributes)
        for child in self._children:
            child.save()

    def load(self, path, mf=None):
        if not mf:
            mf = {}
        EDLUnit.load(self, path, mf)

        for d in os.listdir(self.path):
            unit_path = os.path.join(self.path, d)
            if not os.path.isdir(unit_path):
                continue
            mf_path = os.path.join(unit_path, 'manifest.toml')
            if not os.path.isfile(mf_path):
                continue

            with open(os.path.join(mf_path), 'r', encoding='utf-8') as f:
                mf = toml.load(f)

            unit_type = mf.get('type')
            if unit_type == 'group':
                unit = EDLGroup()
            elif unit_type == 'dataset':
                unit = EDLDataset()
            else:
                raise EDLError(
                    'EDL unit type "{}" is unknown, data can not be loaded.'.format(unit_type)
                )
            unit.load(unit_path, mf)
            self.add_child(unit)
