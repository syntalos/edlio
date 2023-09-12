Examples of using EDL with `edlio`
##################################

To easily read data from EDL directories, the Python module `edlio` exists.
Due to the simple structure of EDL, support for it can easily be implemented
in any other language as well.

This document contains a few examples of how to use `edlio`.

Simple EDL reading example
==========================

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
==============================

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
    y_sig = []

    # read each data file, and concatenate all data to a large chunk
    for intan in dset.read_data(do_timesync=True):
        x_time.append(intan.sync_times)
        y_sig.append(intan.digin_channels_raw[0] * 1)

    x_time = np.concatenate(x_time)
    y_sig = np.concatenate(y_sig)

    # plot the result
    plt.figure()
    plt.plot(x_time, y_sig)
    plt.show()

