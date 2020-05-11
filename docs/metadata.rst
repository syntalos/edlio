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

The following toplevel keys must be present in every ``manifest.toml`` file:

``format_version``
------------------

A string containing the version of the EDL specification used to create this unit and metadata. May be used in future
in case changes are made to EDL.

``type``
--------

A string denoting the type of this organizational unit. May be one of ``collection``, ``group`` or ``dataset``, depending
on the respective unit type. Some unit types may require the presence of additional metadata.

``collection_id``
-----------------

A Universally unique identifier (UUID) version 4 which is unique for the collection that the respective unit is part of.
This ID is purposefully not human-readable. It is intended as a unique identifier for the given experiment, to be used
by data processing pipelines and other programs handling the data.

Within EDL, the last characters of this UUID may also be used in names for data, to make it possible to infer where the
data originated from in case a user copied it out of the EDL layout and sent it somewhere else without its metadata.

In case no collection UUID exists (yet), the ID string may be an invalid UUID consisting only of zeros.

``time_created``
----------------

The creation time of this EDL unit, as an `RFC 3339 <https://tools.ietf.org/html/rfc3339>`_ formatted date-time with offset.
The offset must be present in case the data is shifted between group members in different timezones. For this field, TOMLs native
date-time type support is used.

Collections
===========

TODO

.. code-block:: toml

    collection_id = "49db9875-c0a2-4f70-8ba4-ec00a4e6be9c"
    format_version = "1"
    generator = "Syntalos 1.0"
    time_created = 2020-05-08T17:23:06.000662+02:00
    type = "collection"

Groups
======

TODO

Datasets
========

TODO

Custom Metadata
===============

TODO

Syntalos Metadata
=================

TODO
