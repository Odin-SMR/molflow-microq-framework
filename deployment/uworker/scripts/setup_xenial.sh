#!/bin/bash -x

set -e

sudo apt-get update -qq -y
sudo apt-get upgrade -qq -y
sudo apt-get -y -qq install wget curl --no-install-recommends
