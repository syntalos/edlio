# -*- coding: utf-8 -*-
#
# Copyright (C) 2019-2020 Matthias Klumpp <matthias@tenstral.net>
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

import pytest


@pytest.fixture(scope='session')
def samples_dir():
    """
    Prepare samples in the samples directory and return full path to the directory.
    """

    import lzma

    from . import source_root

    smpldir = os.path.join(source_root, 'tests', 'samples')
    if not os.path.isdir(smpldir):
        raise Exception('Unable to find test samples directory in {}'.format(smpldir))

    # unpack any xz files that we just compress for efficient storage,
    # but need in their raw form for testing
    raw_fnames = [os.path.join(smpldir, 'blink1', 'intan-signals', 'a870_data_210208_181726.rhd')]
    for raw_fname in raw_fnames:
        with open(raw_fname, 'wb') as f:
            f.write(lzma.open(raw_fname + '.xz').read())

    yield smpldir

    # cleanup
    for raw_fname in raw_fnames:
        os.remove(raw_fname)
