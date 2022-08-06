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

from .group import EDLGroup


class EDLCollection(EDLGroup):
    '''
    An EDL Collection
    '''

    def __init__(self, name=None):
        '''
        Create a new EDL collection.

        If the collection has no name and path set, it can not be saved
        to disk.

        Parameters
        ----------
        name
            Name of this collection, or None
        '''
        EDLGroup.__init__(self, name)

    @property
    def generator_id(self) -> str:
        '''Identification string of the software which generated this EDL unit.'''
        return self._generator_id

    @generator_id.setter
    def generator_id(self, v: str):
        self._generator_id = v

    @property
    def collection_idname(self) -> str:
        '''
        Retrieve a human-readable string for this collection which is
        most likely (but not guaranteed to be) unique.
        If this collection has no properties set, the value of this property
        may be None or empty.
        The format of the returned string is arbitrary and should not be parsed.
        '''
        parts = []
        subject_id = self.attributes.get('subject_id')
        if subject_id:
            parts.append(str(subject_id))
        if self.name:
            parts.append(str(self.name))
        if self.time_created:
            parts.append(self.time_created.strftime('%y-%m-%d'))
        if self.collection_id:
            parts.append(str(self.collection_id)[:6])

        return '_'.join(parts).replace(' ', '')
