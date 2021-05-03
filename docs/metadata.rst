Metadata
########

EDL metadata and data compliance is what makes a regular directory hierarchy into an structure
readable by tools supporting EDL.
In order for a directory to be recognized as part of an EDL hierarchy, a ``manifest.toml`` file
must be present.

Directory/Unit Names
====================

A directory name is also the name of the EDL unit, be it a collection, group or dataset.
In order to be somewhat sane and also portable to non-UNIX systems, some constraints apply
to directory naming:

* Only printable characters may be used.
* No special characters and punctuation is permitted, except for dots, hyphens, underscores and plus-signs (``.-_+``).
* Names must not start or end with a dot.
* Unicode characters are permitted, but users are encouraged to stick to ASCII characters if possible.
  EDL implementations must convert from the system's native encoding to UTF-8 when reading names.
* The maximum length of a name is capped at 255 characters.
* MS-DOS device names (such as `AUX`) are forbidden, as Windows will not permit directories of that name.
* EDL names are handled in a case-sensitive way, yet two units in the same directory must not have the same
  name when both are converted to lowercase letters.
* It is recommended to not start unit names with a number, and encouraged to only use lowercase names

Common Metadata
===============

The ``manifest.toml`` file contains basic information about an organizational unit in EDL.
It must be a valid `TOML <https://github.com/toml-lang/toml>`_ 1.0 file and pass TOML
compliance tests.
A minimal file may look like this:

.. code-block:: toml

    format_version = "1"
    type = "group"
    collection_id = "49db9875-c0a2-4f70-8ba4-ec00a4e6be9c"
    time_created = 2020-05-08T17:23:06+02:00

The following toplevel keys can or must be present in every ``manifest.toml`` file:

``format_version``
------------------

*[required, string]* A string containing the version of the EDL specification used to create this unit and metadata. May be used in future
in case changes are made to EDL.

``type``
--------

*[required, string]* A string denoting the type of this organizational unit. May be one of ``collection``, ``group`` or ``dataset``, depending
on the respective unit type. Some unit types may require the presence of additional metadata.

``collection_id``
-----------------

*[required, string]* A Universally unique identifier (UUID) version 4 which is unique for the collection that the respective unit is part of.
This ID is purposefully not human-readable. It is intended as a unique identifier for the given experiment, to be used
by data processing pipelines and other programs handling the data.

Within EDL, the last characters of this UUID may also be used in names for data, to make it possible to infer where the
data originated from in case a user copied it out of the EDL layout and sent it somewhere else without its metadata.

In case no collection UUID exists (yet), the ID string may be an invalid UUID consisting only of zeros.

``time_created``
----------------

*[required, datetime]* The creation time of this EDL unit, as an `RFC 3339 <https://tools.ietf.org/html/rfc3339>`_ formatted date-time with offset.
The offset must be present in case the data is shifted between group members in different timezones. For this field, TOMLs native
date-time type support is used.

``generator``
-------------

*[optional, string]* Name and version of the tool that generated this metadata/data/EDL unit.

Collections
===========

Collections are the root of each EDL directory tree. Their ``type`` is ``collection``.
In addition to the common keys in their ``manifest.toml``, they may also contain the following entries:

``generator``
-------------

*[recommended, string]* Name and version of the tool that generated this data collection, if there was one.
This is usually used by tools like Syntalos.

``authors``
-----------

*[optional, array of tables]* Array of tables with the author names as string values in ``name`` keys and author
email addresses as string values in ``email`` keys. This can be useful to track authorship of who generated
the data originally, or who edited it later.

Manifest Example:
-----------------

.. code-block:: toml

    collection_id = "49db9875-c0a2-4f70-8ba4-ec00a4e6be9c"
    format_version = "1"
    generator = "Syntalos 1.0"
    time_created = 2020-05-08T17:23:06.000662+02:00
    type = "collection"

    [[authors]]
    email = "rick@c137.local"
    name = "Rick Sanchez"

    [[authors]]
    email = "morty@c137.local"
    name = "Morty Smith"

Groups
======

Groups are named containers for more groups or datasets. Their ``type`` is ``group``.
They may contain any of the common keys in their ``manifest.toml`` metadata.

Datasets
========

Datasets are EDL units which contain the actual experiment data. they are leafs in the directory
hierarchy. Their ``type`` is ``dataset``.
In addition to the common keys in their ``manifest.toml``, they may also contain the following entries:

``data``
--------

*[required, table]* This block briefly describes the data of the dataset. It may have the following keys:

``media_type``
^^^^^^^^^^^^^^

*[maybe-optional, string]* The MIME/`MediaType <https://en.wikipedia.org/wiki/Media_type>`_ of the contained data, if one is associated
with the given media. In case no media type can be determined, the ``file_type`` key becomes a required key. Either the ``media_type``
or ``file_type`` key or both must be present.

``file_type``
^^^^^^^^^^^^^

*[maybe-optional, string]* The file-type of the contained data. This is usually the file extension of the contained data without the dot,
but may be any agreed-on string to indicate a specific type of data. In case a ``media_type`` could be determined, this key becomes optional,
otherwise it is required. Either the ``media_type`` or ``file_type`` key or both must be present.

``summary``
^^^^^^^^^^^^^

*[optional, string]* This optional field can contain a human-readable description string that can provide some information about
what the files are about. Values could be for example "Videos recorded from the overview camera" or "Electrophysiology data from silicon probes".

``parts``
^^^^^^^^^

*[required, array of tables]* Array of tables with one entry for data part. Since the data is potentially very big, DAQ tools may decide to chunk
it into smaller bits to make the impact of data corruption while writing less severe and to permit data processing in smaller chunks.
This is especially common with video files.
In case data is not chunked, this array is still present, but contains only one entry. Each table entry must have a ``fname`` key with the filename
of the respective chunk as string value. The filename must be a path relative to the dataset directory (which almost always means it is the file
base name, without any path segment). An entry may have an optional start-at-zero ``index`` key with an integer value attached to it as well, to make
the ordering of the individual chunks explicit. In case the index is not explicitly defined, data will be read in list order. Explicit indexing is
occasionally useful when whole chunks may be transparently taken out of the data analysis.

``data_aux``
------------

*[optional, table]* This block describes auxiliary data to the primary data of this dataset. This may for example be a frame-number to timestamp mapping
file for a video file, or time-sync information files. Auxiliary data is usually so tightly coupled to its primary data that you will never want to have it
separate from the primary data in its own dataset.
A ``data_aux`` table follows the same semantics as a ``data`` table, with the same key names and permitted values.


Manifest Example:
-----------------

.. code-block:: toml

    collection_id = "49db9875-c0a2-4f70-8ba4-ec00a4e6be9c"
    format_version = "1"
    time_created = 2020-05-08T17:23:06+02:00
    type = "dataset"

    [data]
    media_type = "video/x-matroska"

        [[data.parts]]
        fname = "video_1.mkv"
        index = 0

        [[data.parts]]
        fname = "video_2.mkv"
        index = 1

    [data_aux]
    media_type = "text/csv"

        [[data_aux.parts]]
        fname = "video_1_timestamps.csv"
        index = 0

        [[data_aux.parts]]
        fname = "video_2_timestamps.csv"
        index = 1


Custom Metadata
===============

Custom metadata follows no defined specification. Users and programs may add it arbitrarily as TOML 1.0 data to ``attributes.toml`` files which are
shipped alongside the well-defined ``manifest.toml`` files in the same directory. Usually attributes files contain additional metadata describing an
actual dataset (such as explanations for an array dataset, or additional information for an experiment run).

Syntalos Metadata
=================

The `Syntalos <https://github.com/bothlab/syntalos>`_ DAQ system uses the ``attributes.toml`` file of the `collection` root node it creates to add a
bunch of additional metadata.
This behavior is restricted to the ``attributes.toml`` file of the main collection, all other attributes files are exclusively in the domain of Syntalos
modules without interference from the main engine.

The additional metadata includes the following fields:

``machine_node``
----------------

*[required, string]* A string consisting of the recording machine's hostname followed by the operating system name and version in square brackets.

``recording_length_msec``
-------------------------

*[required, number]* Full length of the recording run in milliseconds.

``subject_id``
--------------

*[optional, string]* Name of the test subject, as entered in the "Subject" form in Syntalos.

``subject_group``
-----------------

*[optional, string]* Group of the test subject.

``subject_comment``
-------------------

*[optional, string]* Experimenter comment for the test subject.

``success``
-----------

*[required, boolean]* Boolean, indicating whether the run was successful or failed.

``failure_reason``
------------------

*[optional, string]* In case ``success`` was `false`, this field contains a string with the last error message received by the system,
and which module emitted it.

``modules``
-----------

*[required, array of tables]* List of all Syntalos modules that were active during the run. The ``id`` key contains the machine-readable
string ID of the respective module, while the ``name`` key contain the user-defined name that was given to the module during the run.


Example Attributes File
-----------------------

.. code-block:: toml

    machine_node = "glados [Debian 10]"
    recording_length_msec = 1078556.0
    subject_id = "TAX-010"
    success = true

    [[modules]]
    id = "camera-tis"
    name = "TIS Camera"

    [[modules]]
    id = "miniscope"
    name = "Miniscope"

    [[modules]]
    id = "canvas"
    name = "MS Canvas"

    [[modules]]
    id = "videorecorder"
    name = "Overview Recorder"

    [[modules]]
    id = "videorecorder"
    name = "Scope Recorder"

    [[modules]]
    id = "canvas"
    name = "OV Canvas"
