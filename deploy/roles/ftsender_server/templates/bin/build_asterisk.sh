#!/bin/bash

set -e

cd /home/asterisk

tar xzf {{ DOWNLOAD_ASTERISK_FILENAME }}

cd {{ DOWNLOAD_ASTERISK_EXTRACT_DIRNAME }}

./configure --prefix=/opt/asterisk-11 CFLAGS="-march=i586"

make -j 10
make install
make samples
