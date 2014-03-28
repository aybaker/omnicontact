#!/bin/bash

BASEDIR=$( cd $(dirname $0) ; pwd)

if [ -z "${VIRTUAL_ENV}" -a -d ${BASEDIR}/virtualenv ] ; then
	. ${BASEDIR}/virtualenv/bin/activate
fi

uwsgi \
	--module=fts_web.wsgi:application \
	--env DJANGO_SETTINGS_MODULE=${DJANGO_SETTINGS_MODULE:-fts_web.settings} \
	--master \
	--processes=${UWSGI_PROCESSES:-5} --enable-threads \
	--home=${VIRTUAL_ENV} \
	--http=${UWSGI_HTTP:-127.0.0.1:8080} \
    --python-path=${BASEDIR} \
	--static-map /static=${BASEDIR}/fts_web/static \
	--mule=${BASEDIR}/fts_daemon/poll_daemon.py \
	$*
