#!/bin/bash

set -e

wget {{RPM_REPO_USB_MODESWITCH}}
wget {{RPM_REPO_USB_MODESWITCH_DATA}}

rpm -ivh --nodeps usb_modeswitch-1.1.5-1.el6.rf.i686.rpm
rpm -ivh --nodeps usb_modeswitch-data-20101202-1.el6.rf.noarch.rpm