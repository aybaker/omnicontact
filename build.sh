#!/bin/bash

#
# Script de build y deploy para FTSender
# Autor: Horacio G. de Oro <hgdeoro@gmail.com>
# Requiere: virtualenv activado
#
# Otros comandos interesantes:
#  $ ansible -m setup hostname
#      Para visualizar facts
#

if [ "$VIRTUAL_ENV" = "" ] ; then
        echo "ERROR: virtualenv (o alguno de la flia.) no encontrado"
        exit 1
fi

set -e

cd $(dirname $0)

TMP=/dev/shm/ftsender-build

if [ -e $TMP ] ; then
	rm -rf $TMP
fi

mkdir -p $TMP/app
echo "Directorio temporal: $TMP/app"

echo "Creando bundle..."
git archive --format=tar $(git rev-parse HEAD) | tar x -f - -C $TMP/app

echo "Eliminando archivos innecesarios..."
rm -rf $TMP/app/fts_tests
rm -rf $TMP/app/docs
rm -rf $TMP/app/deploy
rm -rf $TMP/app/build
rm -rf $TMP/app/run_coverage*
rm -rf $TMP/app/run_sphinx.sh

echo "Creando archivo de version..."
cat > $TMP/app/fts_web/version.py <<EOF

#
# Archivo autogenerado
#

FTSENDER_COMMIT="$(git rev-parse HEAD)"
FTSENDER_BUILD_DATE="$(date)"
FTSENDER_AUTHOR="$(id -un)@$(hostname -f)"

if __name__ == '__main__':
    print FTSENDER_COMMIT


EOF

export DO_CHECKS="${DO_CHECKS:-no}"

echo "Ejecutando Ansible"
ansible-playbook deploy/playbook.yml --extra-vars "BUILD_DIR=$TMP/app" $*

