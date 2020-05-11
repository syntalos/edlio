Data Storage Formats
####################

While EDL defines the layout data is stored in and metadata to describe it, it also limits the formats how the data
itself is stored. This is done to make implementations simpler and reduce failure modes.

Policy Requirements
===================

In order for a format to be considered as recommended in EDL, it has to fulfill the following basic criteria:

* Readable and writable with free and open-source software tools
* Cross-platform readability and writability
* Does not duplicate fucntionality of an already existing, accepted format. We explicitly do not want to add
  multiple formats to achieve the same goal, unless there is a significant benefit to do so.

In addition to the essential criteria, there are also a bunch of nice-to-have things:

* The format should be patent-free in all major jurisdictions. There should be no risk in having to pay patent
  fees at any time (this would be a hard requirement, but patents are a difficult matter to research, and we
  already made an exception for the HEVC video codec).
* The format should have implementations in C/C++, Python, or other popular languages in research available.
* The format should be established and widely used.

The following sections outline the existing EDL format requirements for different media types.

Videos
======

All videos must be stored in the `Matroska <https://www.matroska.org/>`_ media container format.
This container format is extensible, flexible, an open standard and there is almost no codec unsupported with it.

Lossless video should be encoded using the `FFV1 <https://en.wikipedia.org/wiki/FFV1>`_ codec, version 3 (or higher).
FFV1 is recommended for data archival, fast and relatively efficient (considering the data has to be losslessly compressed).
Additional codec options for lossless video are VP9 or AV1, but if possible FFV1 should be preferred.

Lossy video may be compressed using the `AV1 <https://aomedia.org/av1-features/>`_, `VP9 <https://www.webmproject.org/vp9/>`_
or `HEVC <https://en.wikipedia.org/wiki/High_Efficiency_Video_Coding>`_ video codecs, in this order of preference.
HEVC is not royalty free for all use-cases and patent encumbered, but due to its wide support, hardware encoding and decoding
is already readily available, which makes it a fast option for live media encoding (a state that the AV1 codec has not reached yet.
VP9 is often a good middle ground).

Tables
======

Tables may be stored as text in `text/comma-separated-values` (.csv) files. CSV files as used by EDL must be semicolon-separated,
UTF-8 encoded text documents. Numbers encoded in text must not be padded with zeros or use abbreviations. The machine locale `C`
(`English/UnitedStates`) should be used for encoding. Decimal separator is the dot, digit group separators must not be used.

Dates must and times must be stored in RFC 822 compliant form. Duration integers are assumed to be milliseconds unless the unit
is explicitly specified in a table header.

Arrays
======

Arrays/Matrices should preferrably be stored as NumPy .npz files (multiple arrays) or .npy binary files.
The document `numpy.lib.format <https://numpy.org/doc/stable/reference/generated/numpy.lib.format.html>`_
describes the binary format in detail.

Only scalar numeric types are permitted for NPY arrays for the moment, pickling Python objects into NPY arrays
is forbidden as doing so greatly reduces compatibility with other tools.

Time Sync Files
===============

Time Sync Files (extension: .tsync) are binary files created by `Syntalos <https://github.com/bothlab/syntalos>`_ which can be used
to align timestamps in post processing in case there was a timestamp divergence due to divergent clocks in unsynchronized DAQ devices.

TODO: Document the .tsync binary format here.

Electrophysiology
=================

Currently, the `Intan Technologies <http://intantech.com>`_  "Tranditional" RHD format version 1.3 is used exclusively for
raw electrophysiology data.
It is very fast and efficient to write during data acquisition, while also being a simple binary format that is easy to read
in many programming languages and that is widely supported.

Variants of the RHD format other than its traditional variant are unsupported.
The RHD format in all its variants is described in detail in the
`RHD Format Specification <http://intantech.com/files/Intan_RHD2000_data_file_formats.pdf>`_.
