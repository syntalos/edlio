Examples of using EDL with `edlio`
##################################

To easily read data from EDL directories, the Python module `edlio` exists.
Due to the simple structure of EDL, support for it can easily be implemented
in any other language as well.

This document contains a few examples of how to use `edlio`.

Simple EDL reading example
==========================

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
        dcoll.attributes.get('recording_length_msec', 'unknown'))

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
