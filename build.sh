#!/bin/bash

set -e

cd $(dirname $0)

echo "Creando archivo de version..."
cat > build/ftsender_version.py <<EOF

#
# Archivo autogenerado
#

FTSENDER_COMMIT="$(git rev-parse HEAD)"
FTSENDER_BUILD_DATE="$(date)"
FTSENDER_AUTHOR="$(id -un)@$(hostname -f)"

if __name__ == '__main__':
    print FTSENDER_COMMIT


EOF

echo "Creando bundle..."
git archive --format=tar --prefix=ftsender/ $(git rev-parse HEAD) | gzip > build/ftsender.tar.gz

echo "Ejecutando Ansible"
ansible-playbook deploy/playbook.yml $*

