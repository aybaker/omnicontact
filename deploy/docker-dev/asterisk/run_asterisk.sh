#!/bin/bash

BASEDIR=$(cd $(dirname $0); pwd)

. $BASEDIR/../../virtualenv-fig/bin/activate

cd $BASEDIR/..

fig run asterisk

