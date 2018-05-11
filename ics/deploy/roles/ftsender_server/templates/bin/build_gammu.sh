#!/bin/bash

set -e

cd /opt/gammu

tar -zxvf {{ DOWNLOAD_GAMMU_FILENAME }}

cd {{ DOWNLOAD_GAMMU_EXTRACT_DIRNAME }}

mkdir build
cd build
cmake ..
make
make -i test >> gammu.log
sudo make install >> gammu.log
