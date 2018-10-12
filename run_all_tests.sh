#!/bin/sh

# This script is run by jenkins jobs that uses the diff test template job or
# the build master template job.
set -e

virtualenv --python=python2 env
export VIRTUAL_ENV="${PWD}/env"
export PATH="${PWD}/env/bin:${PATH}"
export PATH="/usr/lib/chromium-browser:${PATH}"
pip install -r test-requirements.txt
xvfb-run py.test --runslow --runsystem --junitxml=result.xml $*
