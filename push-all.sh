#!/bin/bash

set -e
set -u
set -x

BASEDIR=$(cd $(dirname $0) ; pwd)

cd $BASEDIR

git push --all origin
git push --tags origin
git push --tags freetech
git push --all freetech

set +x

echo ""
echo ""
echo " PUSH OK"
echo ""
echo ""
