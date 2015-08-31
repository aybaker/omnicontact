#!/bin/bash
cd /opt/gammu/{{ DOWNLOAD_GAMMU_EXTRACT_DIRNAME }}/build
sudo make install >> gammu.log
