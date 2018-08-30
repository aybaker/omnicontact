#!/bin/bash

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#
# Script para deployar en servidores, por si hace falta iniciar
#  el servicio de FTS manualmente en vez de a travez del script
#  de inicio.
#
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

/home/ftsender/deploy/virtualenv/bin/uwsgi \
    --module=fts_web.wsgi:application \
    --env DJANGO_SETTINGS_MODULE=fts_web.settings \
    --master \
    --processes=5 \
    --enable-threads \
    --home=/home/ftsender/deploy/virtualenv \
    --http=0.0.0.0:{{ UWSGI_HTTP_PORT }} \
    --uwsgi-socket=0.0.0.0:{{ UWSGI_UWSGI_PORT }} \
    --python-path=/home/ftsender/deploy/app \
    --python-path=/home/ftsender/deploy/local \
    --static-map /static=${BASEDIR_WEB}/fts_web/static \
    --pidfile /home/ftsender/deploy/run/fts-uwsgi.pid \
    --die-on-term \
    --master-fifo /home/ftsender/deploy/run/.uwsgi-fifo \
    $*