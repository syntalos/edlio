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

import importlib

# Determine which loader is responsible for which file type.
DATA_LOADERS = {
    'video': 'edlio.dataio.video',
    'tsync': 'edlio.dataio.tsyncfile',
    'csv': 'edlio.dataio.csvdata',
    'rhd': 'edlio.dataio.intan',
}


def load_dataio_module(what):
    path = DATA_LOADERS[what]
    mod = importlib.import_module(path)
    return mod.load_data
