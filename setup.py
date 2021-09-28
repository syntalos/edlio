#!/usr/bin/env python3

import os
import pathlib
import toml
from edlio import __appname__, __version__
from setuptools import setup

source_root = os.path.dirname(__file__)
if not os.path.isabs(__file__):
    thisfile = os.path.dirname(os.path.normpath(os.path.join(os.getcwd(), __file__)))

packages = [
    'edlio',
    'edlio.dataio',
]

pyproject_data = toml.loads(pathlib.Path('pyproject.toml').read_text())

setup(
    name=__appname__,
    version=__version__,
    author="Matthias Klumpp",
    author_email="matthias@tenstral.net",
    description='Module to work with data in an Experiment Directory Layout (EDL) structure',
    url="https://edl.readthedocs.io/",
    license=pyproject_data['project']['license']['text'],
    long_description=open(os.path.join(source_root, 'README.md')).read(),
    long_description_content_type='text/markdown',

    install_requires=pyproject_data['project']['dependencies'],
    python_requires=pyproject_data['project']['requires-python'],
    platforms=['any'],

    packages=packages
)
