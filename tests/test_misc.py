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

import string
from pathlib import Path

import pytest
import tomlkit as toml

import edlio
from edlio import (
    EDLError,
    EDLGroup,
    EDLDataset,
    EDLDataFile,
    EDLDataPart,
    EDLCollection,
)
from edlio.utils import listify, sanitize_name


def test_sanitize_name_replaces_path_separators() -> None:
    assert sanitize_name('a/b\\c:d') == 'a_b_cd'


def test_sanitize_name_strips_non_printable() -> None:
    # accented/non-ASCII characters are not in string.printable and get dropped
    assert sanitize_name('héllo') == 'hllo'


def test_sanitize_name_none_and_empty() -> None:
    assert sanitize_name(None) is None
    assert sanitize_name('') is None


def test_sanitize_name_falls_back_to_random_when_empty_after_filter() -> None:
    fallback = sanitize_name('日本語')
    assert fallback is not None
    assert len(fallback) == 4
    assert all(c in (string.ascii_uppercase + string.digits) for c in fallback)


def test_listify() -> None:
    assert listify('Jane Doe') == ['Jane Doe']

    src = ['a', 'b']
    assert listify(src) is src
    assert listify(('a', 'b')) == ['a', 'b']
    assert listify(42) == [42]

    assert listify(None) == []
    assert listify('') == []
    assert listify([]) == []


def test_datapart_ordering_and_equality() -> None:
    parts = [EDLDataPart('c', 2), EDLDataPart('a', 0), EDLDataPart('b', 1)]
    parts.sort()
    assert [p.index for p in parts] == [0, 1, 2]
    assert EDLDataPart('x', 1) == EDLDataPart('y', 1)
    assert EDLDataPart('x', 0) < EDLDataPart('y', 1)
    assert EDLDataPart('x', 0) != 'not-a-part'


def test_add_child_propagates_collection_id_and_path() -> None:
    coll = EDLCollection('rec')
    coll.root_path = Path('/tmp/does-not-need-to-exist')

    group = EDLGroup('grp')
    coll.add_child(group)
    assert group.parent is coll
    assert group.collection_id == coll.collection_id
    assert group.root_path == coll.path

    dset = EDLDataset('dd')
    group.add_child(dset)
    assert dset.parent is group
    assert dset.collection_id == coll.collection_id
    assert dset.root_path == group.path


def test_change_name_in_memory_unit() -> None:
    # renaming a unit that was never saved must not raise (no path to move)
    dset = EDLDataset('old')
    dset.change_name('new')
    assert dset.name == 'new'


def test_change_name_on_disk(tmp_path: Path) -> None:
    coll = EDLCollection('rec')
    coll.root_path = tmp_path
    dset = coll.dataset_by_name('old', create=True)
    old_dir = dset.path
    assert old_dir.is_dir()

    dset.change_name('renamed')
    assert dset.name == 'renamed'
    assert dset.path.is_dir()
    assert dset.path.name == 'renamed'
    assert not old_dir.exists()


def test_load_non_edl_directory_raises(tmp_path: Path) -> None:
    with pytest.raises(EDLError):
        edlio.load(tmp_path)


def _write_manifest(path: Path, **fields: object) -> None:
    path.mkdir(parents=True, exist_ok=True)
    with open(path / 'manifest.toml', 'w', encoding='utf-8') as f:
        toml.dump(dict(fields), f)


def test_load_unknown_type_raises(tmp_path: Path) -> None:
    unit_dir = tmp_path / 'weird'
    _write_manifest(unit_dir, format_version='1', type='banana', time_created='2024-01-01 00:00:00')
    with pytest.raises(EDLError):
        edlio.load(unit_dir)


def test_load_unsupported_format_version_raises(tmp_path: Path) -> None:
    unit_dir = tmp_path / 'fromfuture'
    _write_manifest(
        unit_dir, format_version='999', type='dataset', time_created='2024-01-01 00:00:00'
    )
    with pytest.raises(EDLError):
        edlio.load(unit_dir)


def test_read_without_type_association_raises() -> None:
    df = EDLDataFile(None)
    df.parts.append(EDLDataPart('x.bin'))
    with pytest.raises(EDLError):
        df.read()


def test_read_unknown_type_raises() -> None:
    df = EDLDataFile(None, file_type='nonsense')
    df.parts.append(EDLDataPart('x.nonsense'))
    with pytest.raises(EDLError):
        df.read()


def test_tsync_corruption_is_detected(tmp_path: Path, samples_dir: Path) -> None:
    from edlio.dataio.tsyncfile import TSyncFile

    src = samples_dir / 'tsync' / 'syntalos-3.x-valid.tsync'
    raw = bytearray(src.read_bytes())

    # flip a byte deep in the data region; this must trip the block checksum
    # (or terminator) validation rather than silently returning wrong data
    raw[len(raw) // 2] ^= 0xFF
    corrupt = tmp_path / 'corrupt.tsync'
    corrupt.write_bytes(raw)

    with pytest.raises(ValueError):
        TSyncFile(corrupt)
