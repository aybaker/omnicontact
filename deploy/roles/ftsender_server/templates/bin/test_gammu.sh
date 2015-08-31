#!/bin/bash
cd /opt/gammu/{{ DOWNLOAD_GAMMU_EXTRACT_DIRNAME }}/build
make -i test >> gammu.log
