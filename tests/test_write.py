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

from pathlib import Path

import edlio
from edlio import EDLDataFile


def _build_collection(root: Path) -> edlio.EDLCollection:
    coll = edlio.EDLCollection('myrec')
    coll.root_path = root
    coll.generator_id = 'edlio-tests/1.0'
    coll.attributes['subject_id'] = 'mouse01'

    videos = coll.group_by_name('videos', create=True)
    dset = videos.dataset_by_name('camera', create=True)

    # main data: a video, identified by a media type
    dset.data.media_type = 'video/x-matroska'
    _, video_path = dset.data.new_part('camera.mkv')
    video_path.write_bytes(b'not-a-real-video')

    # aux data: a tsync file, identified by a *file type* (different kind than
    # the main data - this is what regressed bug #1 in _serialize_data_md)
    aux = EDLDataFile(dset.path, file_type='tsync')
    _, tsync_path = aux.new_part('camera.tsync')
    tsync_path.write_bytes(b'not-a-real-tsync')
    dset.add_aux_data(aux)

    return coll


def test_create_and_save_roundtrip(tmp_path: Path) -> None:
    coll = _build_collection(tmp_path)

    # this must not raise: aux data of a different type-kind than the main data
    # previously made save() crash because a None media_type was serialized.
    coll.save()

    # a collection's root_path is its parent, so it lives in <root>/<name>
    reloaded = edlio.load(tmp_path / 'myrec')
    assert isinstance(reloaded, edlio.EDLCollection)
    assert reloaded.generator_id == 'edlio-tests/1.0'
    assert reloaded.attributes.get('subject_id') == 'mouse01'
    assert reloaded.collection_id == coll.collection_id

    dset = reloaded.group_by_name('videos').dataset_by_name('camera')
    assert dset is not None

    # main data survived
    assert dset.data.media_type == 'video/x-matroska'
    assert [str(p.fname) for p in dset.data.parts] == ['camera.mkv']

    # aux data survived with its own file_type intact (regression guard, bug #1)
    assert len(dset.aux_data) == 1
    assert dset.aux_data[0].file_type == 'tsync'
    assert dset.aux_data[0].media_type is None
    assert [str(p.fname) for p in dset.aux_data[0].parts] == ['camera.tsync']


def test_new_part_works_on_freshly_created_dataset(tmp_path: Path) -> None:
    # A dataset created via *_by_name(create=True) should have a usable base
    # path so that data.new_part() resolves to a concrete on-disk location.
    coll = edlio.EDLCollection('rec')
    coll.root_path = tmp_path
    dset = coll.dataset_by_name('numbers', create=True)

    _, path = dset.data.new_part('values.csv')
    assert path == dset.path / 'values.csv'
    assert list(dset.data.part_paths()) == [dset.path / 'values.csv']


def test_save_dataset_without_parts_omits_data(tmp_path: Path) -> None:
    coll = edlio.EDLCollection('rec')
    coll.root_path = tmp_path
    coll.dataset_by_name('empty', create=True)
    coll.save()

    reloaded = edlio.load(tmp_path / 'rec')
    dset = reloaded.dataset_by_name('empty')
    assert dset is not None
    assert dset.data.parts == []
