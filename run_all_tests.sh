#!/bin/sh

# This script is run by jenkins jobs that uses the diff test template job or
# the build master template job.
set -e

virtualenv env
export VIRTUAL_ENV="${PWD}/env"
export PATH="${PWD}/env/bin:${PATH}"
export PATH="/usr/lib/chromium-browser:${PATH}"
Xvfb :42 -ac &
export DISPLAY=:42
pip install -r test-requirements.txt
py.test --runslow --runsystem --junitxml=result.xml
killall Xvfb
