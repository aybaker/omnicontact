#!/bin/bash

BASEDIR=$(cd $(dirname $0) ; pwd)

if [ -z "${VIRTUAL_ENV}" -a -d ${BASEDIR}/virtualenv ] ; then
	. ${BASEDIR}/virtualenv/bin/activate
fi

if [ -z "$DISABLE_STATIC_MAP" ] ; then
	STATIC_MAP="--static-map /static=${BASEDIR}/dev/static_root"
	echo "Static map: $STATIC_MAP"
else
	echo "SIN STATIC MAP"
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
    --mule=${BASEDIR}/fts_daemon/services/finalizador_vencidas_daemon.py \
    --attach-daemon=${BASEDIR}/dev/celery_worker_finalizar_campana.sh \
    --attach-daemon=${BASEDIR}/dev/celery_worker_esperar_y_finalizar_campana.sh \
    --attach-daemon=${BASEDIR}/dev/run_collectstatic.sh \
    $*
