#!/bin/bash

#
# Shell script para facilitar el deploy de la aplicación desde un servidor de deploy
# Aunque este script esta en Git, en realida debe copiarse al directorio del usuario 'deployer',
#   para que siempre este accesible independientemente de la version en el working directory
#
# Autor: Horacio G. de Oro
#
# Changelog:
#  * 2014-06-12 - Version inicial
#  * 2014-06-13 - Agrega 'git fetch'
#

if [ -z "$VIRTUAL_ENV" ] ; then
	. ~/virtualenv/bin/activate
fi

if [ -z "$1" ] ; then
	echo "ERROR: debe especificar la version (branch, tag o commit)"
	exit 1
fi

VERSION=$1
shift

if [ -z "$1" ] ; then
	echo "ERROR: debe especificar el archivo de inventario"
	exit 1
fi

if [ ! -e "$1" ] ; then
	echo "ERROR: el archivo de inventario no existe"
	exit 1
fi

INVENTORY=$1
shift

set -e

echo ""
echo "Se iniciará deploy:"
echo ""
echo "      Version: $VERSION"
echo "   Inventario: $INVENTORY"
echo ""
echo "Presione ENTER para iniciar deploy..."
read
echo ""

cd ~/ftsenderweb

git clean -fdx

git fetch --prune --tags --force --all -v

git checkout master

git pull origin +master:master

git checkout $VERSION

./build.sh -i $INVENTORY $*

