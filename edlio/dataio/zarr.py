# -*- coding: utf-8 -*-
#
# Copyright (C) 2025-2026 Matthias Klumpp <matthias@tenstral.net>
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

import typing as T
from pathlib import Path

from ..dataset import EDLDataFile


def load_data(
    part_paths: T.Iterable[Path], aux_data_entries: T.Sequence[EDLDataFile]
) -> T.Iterator[T.Any]:
    """Entry point for automatic dataset loading.

    Opens each Zarr store and yields its root group. Callers can access
    arrays and attributes directly via the zarr API.
    """
    try:
        import zarr
    except ImportError as e:
        raise ImportError('Missing optional dependency "zarr". Please install it with pip!') from e

    for store_path in part_paths:
        # We need to open from a local store explicitly, because otherwise, if the local
        # path string contains any URL element like "#" or "?", the Zarr parser will drop
        # it. On newer Zarr versions, passing in a pathlib.Path will work, but we don't
        # want to rely on that just yet.
        store = zarr.storage.LocalStore(store_path)
        yield zarr.open(store, mode='r')
