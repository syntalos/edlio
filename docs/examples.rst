Examples
########

Examples using `edlio`
======================

To easily read data from EDL directories, the Python module `edlio` exists.
Due to the simple structure of EDL, support for it can easily be implemented
in any other language as well.

This document contains a few examples of how to use `edlio`.

Simple EDL reading example
--------------------------

This code snippet reads an EDL collection that has a `generic-camera` dataset
containing a camera video in a `videos` EDL group.

If the camera data has time-sync information in the `tsync` format, the timing data
is loaded automatically and provided as value in ``frame.time``.

.. code-block:: python

    import sys
    import edlio
    import cv2 as cv


    # load our data collection
    dcoll = edlio.load('/path/to/edl/dataset/directory')

    # display some information about this dataset
    print('Loaded data collection {}, created on {}, recording length: {}'.format(
        dcoll.collection_idname,
        dcoll.time_created,
        dcoll.attributes.get('recording_length_msec', 'unknown')))

    # get reference to the "videos" group
    egroup = dcoll.group_by_name('videos')
    if not egroup:
        print('This dataset did not contain a "videos" group!')
        sys.exit(1)

    # get the "generic-camera" dataset
    dset = egroup.dataset_by_name('generic-camera')
    if not dset:
        print('Dataset "generic-camera" was not found in {}.'.format(dcoll.collection_idname))
        sys.exit(1)

    # display all frames from this dataset and their timestamps (if any were found)
    for frame in dset.read_data():
        print('Frame time: {}'.format(frame.time))
        cv.imshow(dset.name, frame.mat)

        if cv.waitKey(25) & 0xFF == ord('q'):
            break


Reading electrophysiology data
------------------------------

The `edlio` library will automatically time-sync Intan electrophysiology data
when data is read. The data itself is made available as an
`IntanRawIO <https://neo.readthedocs.io/en/stable/rawio.html#neo.rawio.IntanRawIO>`_
subclass from the Neo library, and can be used like any other Neo object.

The code below loads all intan files, has them time-synchronized automatically and then displays
an input from the Intan boards digital channel as 1/0 value in a plot.

.. code-block:: python

    import edlio
    import matplotlib.pyplot as plt


    # load our data collection
    dcoll = edlio.load('/path/to/edl/dataset/directory')

    # grab the "intan-signals" dataset
    dset = dcoll.dataset_by_name('intan-signals')

    x_time = []
    y_sig_d = []
    y_sig_a = []

    # read each data file, and concatenate all data to a large chunk
    for nreader in dset.read_data(do_timesync=True):
        x_time.append(nreader.sync_times)

        # read one digital channel
        y_sig_d.append(nreader.digin_channels_raw[0] * 1)
        # read one analog channel
        y_sig_a.append(nreader.get_analogsignal_chunk(stream_index=0,
                                                      channel_names=['A-001']))

    x_time = np.concatenate(x_time)
    y_sig_d = np.concatenate(y_sig_d)
    y_sig_a = np.concatenate(y_sig_a)

    # plot the result
    plt.figure()
    plt.plot(x_time, y_sig_d)
    plt.plot(x_time, y_sig_a)
    plt.show()


Accessing raw tsync data
------------------------

Sometimes data, e.g. a video file, has been processed by a 3rd-party application, and
you need to get the timestamps back without reading all raw data again.

In this case, reading only the tsync data (or any other accompanying auxiliary data)
is possible!
By using the ``read_aux_data(key)`` function of a dataset, you can specify which auxiliary
data you want to load, If there is only one kind, supplying a key is not necessary (which is the majority of cases).
Otherwise you can define the file/data type you want to load as key.

In our case, we load the time sync data for a Miniscope dataset, and display it without ever touching the
original raw video. This data can then be used to map frame numbers to timestamps in a video that
was processed from the raw video (e.g. by tools like Minian or MIN1PIPE).

.. code-block:: python

    import edlio

    # load our data collection
    dcoll = edlio.load('/path/to/edl/dataset/directory')

    # get the miniscope video dataset
    dset = dcoll.group_by_name('videos').dataset_by_name('miniscope')

    # read auxiliary tsync data files - we assume there is only one such file here
    tsync_data = [tsync for tsync in dset.read_aux_data('tsync')]
    assert len(tsync_data) == 1
    tsync = tsync_data[0]

    # print some information
    print('Labels:', tsync.time_labels)
    print('Units:', tsync.time_units)
    print('Creation Date:', tsync.time_created)

    # get a (X, 2) matrix mapping frame numbers to time stamps (in this case,
    # ensure your tsync units and labels match your expectations!)
    print(tsync.times)


Writing an EDL structure
========================

`edlio` can also create EDL structures on disk. You build the
collection/group/dataset hierarchy in memory, register the data files that
belong to each dataset, write their raw bytes to the paths `edlio` hands you,
and finally call ``save()`` to write out all manifests and attributes.

Note that a unit's ``root_path`` is its *parent* directory: a collection named
``myrec`` with ``root_path = '/data'`` is written to ``/data/myrec``.

.. code-block:: python

    import edlio

    # create a collection and give it a location on disk
    coll = edlio.EDLCollection('myrec')
    coll.root_path = '/path/to/output'  # collection ends up in /path/to/output/myrec
    coll.generator_id = 'my-tool/1.0'
    coll.attributes['subject_id'] = 'mouse01'

    # create a nested group and dataset (create=True adds & saves them)
    videos = coll.group_by_name('videos', create=True)
    dset = videos.dataset_by_name('camera', create=True)

    # describe the main data and register a file part. new_part() returns the
    # part and the absolute path you should write the actual bytes to.
    dset.data.media_type = 'video/x-matroska'
    _, video_path = dset.data.new_part('camera.mkv')
    # ... write your encoded video to `video_path` here ...

    # attach auxiliary data of a different kind (e.g. timestamps)
    aux = edlio.EDLDataFile(dset.path, file_type='tsync')
    _, tsync_path = aux.new_part('camera.tsync')
    # ... write the tsync bytes to `tsync_path` here ...
    dset.add_aux_data(aux)

    # write all manifests and attributes to disk
    coll.save()
