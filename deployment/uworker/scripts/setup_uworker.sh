#!/bin/bash -x

set -e

sudo apt-get install -y -qq python-dev python-pip --no-install-recommends

sudo pip install --upgrade pip
sudo pip install setuptools

# TODO: Move these to setup.py
sudo pip install requests ConcurrentLogHandler

wget --no-check-certificate --no-verbose https://jenkins2.molflow.com/job/RESTful%20uQ%20Job%20Server/219/artifact/microq.tar.gz

tar xf microq.tar.gz
rm microq.tar.gz
sudo mv src /app

# TODO: Install in virtual env
cd /app && sudo python setup.py develop

# TODO: Do not run as root
sudo mv /tmp/start_worker.sh /root/start_worker.sh
sudo mv /tmp/uworker.conf /root/uworker.conf
sudo chown root:root /root/start_worker.sh
sudo chown root:root /root/uworker.conf
sudo chmod u+x /root/start_worker.sh
