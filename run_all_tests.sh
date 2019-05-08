#!/bin/sh

# This script is run by jenkins jobs that uses the diff test template job or
# the build master template job.
set -e

npm install
npm update
npm test

export PATH="/usr/lib/chromium-browser:${PATH}"
tox -- --runslow --runsystem "$@"
