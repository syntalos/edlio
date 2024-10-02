# EDL - Experiment Directory Layout

[![QA](https://github.com/bothlab/edlio/actions/workflows/python-qa.yml/badge.svg)](https://github.com/bothlab/edlio/actions/workflows/python-qa.yml)

This repository contains specifications for the "Experiment Directory Layout" (EDL) storage layout as
used by the [Syntalos](https://github.com/bothlab/syntalos) data acquisition tool.

It also contains a Python module, `edlio`, to easily load and save data in an EDL structure
for simplified raw experiment data management.

Check out the [online documentation](https://edl.readthedocs.io/latest/) to learn more about this project!

## Usage

You can install `edlio` using *pip*:
```bash
pip install edlio
```

You can then use it in your projects to load data, for example for a project
that comntains some camera capture data in a `videos` group:

```python
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
```

You can find [more examples in the documentation](https://edl.readthedocs.io/latest/examples.html).
We also provide [full API documentation](https://edl.readthedocs.io/latest/edlio/edlio.html).
