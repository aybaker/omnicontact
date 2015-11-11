#!/bin/bash

#
# Script de build y deploy para FTSender
#
# Autor: Horacio G. de Oro <hgdeoro@gmail.com>
# Requiere: virtualenv activado
#
# Forma de uso:
#
#   ./build.sh -i deploy/hosts-virtual-pruebas
#
# Otros comandos interesantes:
#
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
echo "Usando directorio temporal: $TMP/app..."

echo "Creando bundle usando git-archive..."
git archive --format=tar $(git rev-parse HEAD) | tar x -f - -C $TMP/app

echo "Eliminando archivos innecesarios..."
rm -rf $TMP/app/fts_tests
rm -rf $TMP/app/docs
rm -rf $TMP/app/deploy
rm -rf $TMP/app/build
rm -rf $TMP/app/run_coverage*
rm -rf $TMP/app/run_sphinx.sh


mkdir -p $TMP/appsms
echo "Usando directorio temporal: $TMP/appsms..."

echo "Descargando demonio sms en directorio temporal"
tar -xzf /home/deployer/aplicacionsms/DEMONIO-SMS.tar.gz -C $TMP/appsms

# ----------

echo "Obteniendo datos de version..."
branch_name=$(git symbolic-ref -q HEAD)
branch_name=${branch_name##refs/heads/}
branch_name=${branch_name:-HEAD}

commit="$(git rev-parse HEAD)"
author="$(id -un)@$(hostname -f)"

echo "Creando archivo de version | Branch: $branch_name | Commit: $commit | Autor: $author"
cat > $TMP/app/fts_web/version.py <<EOF

#
# Archivo autogenerado
#

FTSENDER_BRANCH="${branch_name}"
FTSENDER_COMMIT="${commit}"
FTSENDER_BUILD_DATE="$(env LC_ALL=C LC_TIME=C date)"
FTSENDER_AUTHOR="${author}"

if __name__ == '__main__':
    print FTSENDER_COMMIT


EOF

echo "Validando version.py - Commit:"
python $TMP/app/fts_web/version.py

# ----------

export DO_CHECKS="${DO_CHECKS:-no}"

echo "Ejecutando Ansible"
ansible-playbook deploy/playbook.yml --extra-vars "BUILD_DIR=$TMP/app  BUILD_DIR_SMS=$TMP/appsms" $*

