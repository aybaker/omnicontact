#!/bin/bash

# -~-~-~-~-~ 8< 8< -~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~
VIRTUALENV_NAME="virtualenv-fig"
BASEDIR=$(cd $(dirname $0); pwd)
VIRTUALENV_DIR="$BASEDIR/../$VIRTUALENV_NAME"

if [ -d $VIRTUALENV_DIR ] ; then
        . $VIRTUALENV_DIR/bin/activate
else
        which virtualenvwrapper.sh && source $(which virtualenvwrapper.sh)
        workon $VIRTUALENV_NAME
fi

cd $BASEDIR
# -~-~-~-~-~ >8 >8 -~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~

fig run -f fig_integration_testing.yml asterisk /opt/asterisk-11/sbin/asterisk -x reload
