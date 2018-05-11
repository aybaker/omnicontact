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
	--logfile=/tmp/fts-celery-worker-finalizar_campana.log \
	--loglevel=info \
	-Q finalizar_campana \
	--concurrency=1 \
	worker \
	$*
exit $?
