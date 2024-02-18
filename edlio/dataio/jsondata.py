# -*- coding: utf-8 -*-
#
# Copyright (C) 2020-2024 Matthias Klumpp <matthias@tenstral.net>
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
import json
import typing as T


def _read_pandas_extended_json(fname: str | os.PathLike):
    import pandas as pd

    if str(fname).endswith('.zst'):
        try:
            import zstandard as zstd
        except ImportError as e:
            raise ImportError(
                'Missing optional dependency "zstandard". Please install it with pip!'
            ) from e

        with open(fname, 'rb') as f:
            dctx = zstd.ZstdDecompressor()
            zr = dctx.stream_reader(f)
            jd = json.load(zr)
    else:
        with open(fname, 'r', encoding='utf-8') as f:
            jd = json.load(f)

    jd.pop('collection_id')
    jd.pop('time_unit')
    jd.pop('data_unit')
    df = pd.DataFrame(jd.pop('data'), columns=jd.pop('columns'))

    return df


def load_data(part_paths, aux_data_entries, json_schema: T.Optional[str] = None):
    '''Entry point for automatic dataset loading.

    This function is used internally to load JSON data.
    '''
    try:
        import pandas as pd
    except ImportError as e:
        raise ImportError(
            'Missing optional dependency "pandas". Please install it with pip!'
        ) from e

    if json_schema == 'extended-pandas':
        for fname in part_paths:
            yield _read_pandas_extended_json(fname)
    else:
        for fname in part_paths:
            df = pd.read_json(fname, orient='split')
            yield df
