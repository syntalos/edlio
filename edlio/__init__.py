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

__appname__ = "edlio"
__version__ = "0.0.2"

import os
import toml
from .unit import EDLError
from .group import EDLGroup
from .collection import EDLCollection
from .dataset import EDLDataset


__all__ = ['EDLError',
           'EDLGroup',
           'EDLCollection',
           'EDLDataset',
           'load']


def load(path):
    '''Open an EDL unit via its filesystem path'''

    mf_path = os.path.join(path, 'manifest.toml')
    if not os.path.isfile(mf_path):
        raise EDLError('This directory is no valid EDL unit.')

    with open(os.path.join(mf_path), 'r') as f:
        mf = toml.load(f)

    unit_type = mf.get('type')
    if unit_type == 'collection':
        unit = EDLCollection()
    elif unit_type == 'group':
        unit = EDLGroup()
    elif unit_type == 'dataset':
        unit = EDLDataset()
    else:
        raise EDLError('EDL unit type "{}" is unknown, data can not be loaded.'.format(unit_type))

    unit.load(path, mf)
    return unit
