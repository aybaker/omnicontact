#!/bin/bash

# -~-~-~-~-~ 8< 8< -~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~
VIRTUALENV_NAME="virtualenv-fig"
BASEDIR=$(cd $(dirname $0); pwd)
VIRTUALENV_DIR="$BASEDIR/../$VIRTUALENV_NAME"

if [ -d $VIRTUALENV_DIR ] ; then
	. $VIRTUALENV_DIR/bin/activate
else
	workon $VIRTUALENV_NAME
fi

cd $BASEDIR
# -~-~-~-~-~ >8 >8 -~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~

if [ ! -e asterisk/conf-runtime/cdr_pgsql.conf ] ; then
	echo ""
	echo "*** ERROR: no existe asterisk/conf-runtime/cdr_pgsql.conf"
	echo ""
	echo " Creelo, usando 'asterisk/conf-runtime/cdr_pgsql.conf.sample' de referencia"
	echo ""
	exit 1
fi

fig up

