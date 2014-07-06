#!/bin/bash

celery \
	-A fts_daemon.fts_celery_daemon.app \
	--no-color \
	--logfile=/tmp/fts-celery-worker-finalizar_campana.log \
	--loglevel=info \
	-Q finalizar_campana \
	--concurrency=1 \
	--pidfile=/tmp/fts-celery-worker-finalizar_campana.pid \
	worker \
	$*
exit $?
