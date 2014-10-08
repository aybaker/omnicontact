#!/bin/bash

cd $(dirname $0)

if [ ! -e cdr_pgsql.conf ] ; then
	echo "ERROR: no existe '$(pwd)/cdr_pgsql.conf'"
	echo "Use 'cdr_pgsql.conf.sample' de referencia para crear 'cdr_pgsql.conf'"
	exit 1
fi

if [ ! -e yum.conf.extra ] ; then
	echo "ERROR: no existe '$(pwd)/yum.conf.extra'"
	echo "El archivo debe existir, al menos vacio"
	exit 1
fi

docker build -t hgdeoro/fts-asterisk-dev .
