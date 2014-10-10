#!/bin/bash

BASEDIR=$(cd $(dirname $0); pwd)

. $BASEDIR/../virtualenv-fig/bin/activate

cd $BASEDIR

if [ ! -e asterisk/conf-runtime/cdr_pgsql.conf ] ; then
	echo ""
	echo "*** ERROR: no existe asterisk/conf-runtime/cdr_pgsql.conf"
	echo ""
	echo " Creelo, usando 'asterisk/conf-runtime/cdr_pgsql.conf.sample' de referencia"
	echo ""
	exit 1
fi

fig up

