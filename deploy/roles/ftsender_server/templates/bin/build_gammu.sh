#!/bin/bash

set -e

cd /opt/gammu

tar -xvzf {{ DOWNLOAD_GAMMU_FILENAME }}

cd {{ DOWNLOAD_GAMMU_EXTRACT_DIRNAME }}

mkdir build
cd build
cmake ..
make
make test >> gammu.log
make install
