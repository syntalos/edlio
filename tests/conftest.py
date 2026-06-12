# -*- coding: utf-8 -*-
#
# Copyright (C) 2019-2026 Matthias Klumpp <matthias@tenstral.net>
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

import typing as T
from pathlib import Path

import pytest


@pytest.fixture(scope='session')
def samples_dir() -> T.Iterator[Path]:
    """
    Prepare samples in the samples directory and return full path to the directory.
    """

    import lzma

    from . import source_root

    smpldir = source_root / 'tests' / 'samples'
    if not smpldir.is_dir():
        raise RuntimeError('Unable to find test samples directory in {}'.format(smpldir))

    # unpack any xz files that we just compress for efficient storage,
    # but need in their raw form for testing
    raw_fnames = [smpldir / 'blink1' / 'intan-signals' / 'a870_data_210208_181726.rhd']
    for raw_fname in raw_fnames:
        xz_fname = raw_fname.with_suffix(raw_fname.suffix + '.xz')
        raw_fname.write_bytes(lzma.open(xz_fname).read())

    yield smpldir

    # cleanup
    for raw_fname in raw_fnames:
        raw_fname.unlink()
