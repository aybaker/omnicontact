#!/bin/bash

BASEDIR=$( cd $(dirname $0) ; pwd)

if [ -z "${VIRTUAL_ENV}" -a -d ${BASEDIR}/virtualenv ] ; then
	. ${BASEDIR}/virtualenv/bin/activate
fi

if [ -z "$DISABLE_STATIC_MAP" ] ; then
	STATIC_MAP="--static-map /static=${BASEDIR}/fts_web/static"
fi

uwsgi \
    --module=fts_web.wsgi:application \
    --env DJANGO_SETTINGS_MODULE=${DJANGO_SETTINGS_MODULE:-fts_web.settings} \
    --master \
    --processes=${UWSGI_PROCESSES:-5} --enable-threads \
    --home=${VIRTUAL_ENV} \
    --http=${UWSGI_HTTP:-0.0.0.0:8080} \
    --uwsgi-socket=0.0.0.0:8099 \
    --python-path=${BASEDIR} \
    --master-fifo=/tmp/.ftsender-uwsgi-fifo \
    $STATIC_MAP \
    --mule=${BASEDIR}/fts_daemon/poll_daemon/main.py \
    --mule=${BASEDIR}/fts_daemon/fastagi_daemon.py \
    $*
