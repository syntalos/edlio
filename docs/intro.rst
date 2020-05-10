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

TODO

Comparison with Related Projects
================================

TODO
