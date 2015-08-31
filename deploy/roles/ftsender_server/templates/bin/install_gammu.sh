#!/bin/bash
cd /opt/gammu/{{ DOWNLOAD_GAMMU_EXTRACT_DIRNAME }}/build
make install >> gammu.log
