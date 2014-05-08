#!/bin/bash

if [ "$VIRTUAL_ENV" = "" ] ; then
	echo "ERROR: virtualenv (o alguno de la flia.) no encontrado"
	exit 1
fi

cd $(dirname $0)

coverage run --omit='fts_web/migrations/*,fts_web/tests/*,fts_web/sample_settings_local.py,fts_web/wsgi.py' --source='fts_daemon' manage.py test fts_tests
coverage html -d /tmp/fts-coverity --title="Coverage para daemon de FTS"
which gnome-open > /dev/null 2> /dev/null && gnome-open /tmp/fts-coverity/index.html
