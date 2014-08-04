#!/bin/bash

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#
#  Este script esta pensado para ser utilizado en ambiente
#   de desarrollo (para iniciar manualmente los workers),
#   y es usado tambien por /run_uwsgi.sh
#
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

celery \
	-A fts_daemon.fts_celery_daemon.app \
	--no-color \
	--logfile=/tmp/fts-celery-worker-esperar_y_finalizar_campana.log \
	--loglevel=info \
	-Q esperar_y_finalizar_campana \
	--concurrency=4 \
	--pidfile=/tmp/fts-celery-worker-esperar_y_finalizar_campana.pid \
	worker \
	$*
exit $?
