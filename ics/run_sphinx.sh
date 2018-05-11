#!/bin/bash

if [ "$VIRTUAL_ENV" = "" ] ; then
	echo "ERROR: virtualenv (o alguno de la flia.) no encontrado"
	exit 1
fi

cd $(dirname $0)

export PYTHONPATH=$(pwd)
export DJANGO_SETTINGS_MODULE="fts_web.settings"

cd docs
make html

which gnome-open > /dev/null 2> /dev/null && gnome-open _build/html/index.html > /dev/null 2> /dev/null

echo ""
echo "Para rsync:"
echo ""
echo "    rsync -acv --delete docs/_build/html deployer@192.168.99.224:/var/www/html/ftsender/docs/"
echo "        o"
echo "    rsync -e 'ssh -p 24922' -acv --delete docs/_build/html deployer@190.210.28.37:/var/www/ftsender/docs/"
echo ""

