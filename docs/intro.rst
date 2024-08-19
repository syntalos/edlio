Introduction
############

Data storage is of much concern for researchers in every discipline, and a subject
of much debate with lots of solutions written.

At its core, a storage format of experiment data has to provide three things:

1. Provide an organizational structure for data, so it can be found again at a later
   date and be navigated easily by researchers who did not generate the data originally.
2. Permit safe archival of data that will be readable decades in the future and can ideally
   be processed with many existing tools.
3. Store metadata about the experiment and other descriptive information

In addition to that, a storage layout for raw experiment data also has to fulfill a few more
requirements:

4. Support datasets of multiple modalities: Electrophysiology, Tables, Matrices, Video recordings, ...
5. Allow massively parallel write and read access on the level of individual datsets

The EDL format is a specification for a storage layout for experiment data, with primary
focus on neuroscientific data. It was originally devised exclusively for the
`Syntalos <https://github.com/bothlab/syntalos>`_ DAQ system, which has governed many of
its design decisions.

Architecture Overview
=====================

Unlike file-based formats for data storage, EDL uses a hierarchy of directories to organize data into
logical groups. This permits it to not be limited to one mode of data storage, while also taking full
advantage of all performance optimizations done by the operating system at filesystem level when reading or
writing data. Additionally, writing to multiple datasets in parallel is possible naturally by means of
accessing individual files.

Collections, Groups and Datasets
--------------------------------

EDL distinguishes three fundamental organizational units for sorting data: **Collections**,
**Groups** and **Datasets**.
Each one of these units is represented on the filesystem by a directory containing a ``manifest.toml``
file in the `TOML <https://github.com/toml-lang/toml>`_ markup language which describes the unit type
and additional metadata about is contents.

A **Collection** is the highest organizational unit, similar to a file in single-file based data
storage schemes. It defines basic information, like the unique experiment ID and possible authors
of the data collection. A collection is never contained in any other EDL unit type.

A **Group** is a grouping of datasets or other groups. It never contains data on its own, and may
contain more groups for further hierarchical nesting, or datasets.

A **Dataset** contains the actual experiment data in one of the formats permitted in EDL. Dataset
directories represent leafs of the directory tree and will never contain more directories. A dataset
may have a unit of type group or collection as parent.

.. figure:: img/organization_classes.png
    :align: center
    :width: 60%
    :alt: Organizational classes in EDL

    Types of organizational units in EDL in an inheritance hierarchy

Metadata
--------

Metadata is stored in the `TOML <https://github.com/toml-lang/toml>`_ text-based human-readable markup language.
Fields that are generic and specified in EDL are stored in ``manifest.toml`` files in each directory, while the
experimenter can define and add arbitrary custom metadata in a separate ``attributes.toml`` file to describe a group,
collection or dataset.

Data
----

Experiment data must be stored in a set of well-defined formats, only one type of data is permitted per dataset.
In addition to allowing one primary type of data per dataset, EDL also permits the use of one additional "auxiliary"
type of data. This auxiliary data is usually closely tied to the primary data and describes additional information about
it, for example mapping of frame numbers to timestamps for videos, or timesync information for data acquired with Syntalos.

Example
-------

The following graph shows the use of all three organizational unit types in an example directory hierarchy.
Each node represents a new directory.

.. figure:: img/organization_direxample.png
    :align: center
    :width: 100%
    :alt: Schema of an example EDL directory hierarchy

    Schema of an example EDL directory hierarchy

Comparison with Related Projects
================================

HDF5
----

The `Hierarchical Data Format (HDF) <https://en.wikipedia.org/wiki/Hierarchical_Data_Format>`_ is a file format to store
large amounts of data in a single, structured file. Currently, HDF5 is the most-used container format for a variety of
other file formats, and is especially useful to store array data.

While HDF5 is an excellent format to store structured data, and has the advantage of being just one file instead of a
directory structure like EDL, it also has some disadvantages which may make EDL preferrable in some applications:

* Writing in parallel to multiple datasets in a HDF5 file is very slow due to thread synchronization, making HDF5 not a
  great choice for massively parallel data acquisition.
* In case of an error while writing (e.g. due to a crash of the writing process), the entore HDF5 file may be corrupted,
  instead of just one file. EDL is a bit more robust.
* HDF5 has a limited set of ways to compress its array data. EDL, by using file-formats designed for the recorded modalities,
  can compress the stored data a lot more (e.g. by using the FFV1 video codec for video data).

HDF5's advantages over EDL are it being a single file, its wide industry support and there being a single library to load
the entirety of an HDF5 file (while EDL relies on other tools to read the specific data, e.g. FFmpeg or Neo).


Exdir
-----

The `Experimental Directory Structure (Exdir) <https://exdir.readthedocs.io/en/latest/>`_ is an open file format specification for
experimental pipelines. Like EDL, it is modeled using the same abstractions that HDF5 uses as well.

Exdir and EDL are *extremely* similar to each other, and Syntalos used Exdir for a short time. However, there are some key differences:

* EDL uses `TOML <https://toml.io/en/>`_ for metadata and Exdir uses `YAML <https://yaml.org/>`_. While YAML is great to write for
  humans and sometimes less verbose than TOML, it has quite a lot of `abigutities and pitfalls <https://noyaml.com/>`_ for humans and
  programs to run into, which sometimes makes it harder to be used.
* Exdir adheres fairly strictly to the HDF5 abstract data model and the data types that HDF5 supports. While arrays are well-supported
  as Numpy arrays, there are no standards for "raw" datasets (containing videos or images). For use in a DAQ system like Syntalos, the
  "raw" dataset type wpuld have to be massively extended.
* Each Exdir dataset can only contain one format, while EDL supports "auxiliary data" that describes the contained data further and is not
  pure textual TOML metadata. This auxiliary data may for example be timestamps for a video file. In Exdir, this data would had to be split
  into two datasets, which users found very confusing. EDL allows strongly linked data to be kept together in one directory.
* Exdir has no unique ID for the dataset, and also does not mandata the ID to be added as metadata to files contained in its structure.
  This is a feature that we really wanted for EDL, and that was a bit difficult to retrofit into Exdir.

Overall, Exdir is a fine format that simply has a few less features compared to what we needed for Syntalos. Its advantage over EDL
is that is maps a lot more cleanly to HDF5 data structures and probably needs less processing to be converted into HDF5 than EDL would.


NWB
---

The `Neurodata Without Borders <https://www.nwb.org/>`_ format is a HDF5-based file format and structure to store neuroscientific data
and make it easy to be interchanged between many groups in the neuroscientific community.
It being based on HDF5 makes it not very suitable for massively parallel direct-write data acquisition though, which is why Syntalos
and other DAQ systems can't use it directly.

However, some groups do convert EDL into NWB-HDF5 files after the data acquisition has been completed, which is a good approach to get
the best of both worlds.
