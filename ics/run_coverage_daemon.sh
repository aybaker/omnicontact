#!/bin/bash

if [ "$VIRTUAL_ENV" = "" ] ; then
	echo "ERROR: virtualenv (o alguno de la flia.) no encontrado"
	exit 1
fi

cd $(dirname $0)

export SKIP_SELENIUM=1
export FTS_DEBUG=1
export USE_PG=1

coverage run --omit='fts_daemon/migrations/*,fts_daemon/management/*,fts_web/migrations/*,fts_web/tests/*,fts_daemon/tests/*,fts_web/sample_settings_local.py,fts_web/wsgi.py' --source='fts_daemon,fts_web.services,fts_web.reciclador_base_datos_contacto,fts_web.parser,fts_web.models' manage.py test fts_tests fts_web fts_daemon

coverage html -d /tmp/fts-coverity --title="Coverage para daemon de FTS"

which gnome-open > /dev/null 2> /dev/null && gnome-open /tmp/fts-coverity/index.html > /dev/null 2> /dev/null

echo ""
echo "Para rsync:"
echo ""
echo "   rsync -av --delete /tmp/fts-coverity/ deployer@192.168.99.224:/var/www/html/ftsender/coverity"
echo "        o"
echo "   rsync -e 'ssh -p 24922' -acv --delete /tmp/fts-coverity/ deployer@190.210.28.37:/var/www/ftsender/coverity"
echo ""
