#!/bin/sh
set -e

echo "Flake8"
flake8 ./edlio ./tests --show-source --statistics
echo "OK"

echo "Pylint"
python -m pylint -f colorized ./edlio ./tests
python -m pylint -f colorized setup.py
echo "OK"

echo "MyPy"
mypy --pretty edlio
echo "OK"

echo "Black"
black --diff .
