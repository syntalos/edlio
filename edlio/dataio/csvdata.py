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

import csv


def load_data(part_paths, aux_data_entries):
    '''Entry point for automatic dataset loading.

    This function is used internally to load CSV data.
    '''
    for fname in part_paths:
        with open(fname, newline='', encoding='utf-8') as f:
            reader = csv.reader(f, delimiter=';')
            for row in reader:
                yield row
