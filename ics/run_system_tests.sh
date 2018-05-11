#!/bin/bash

if [ "$VIRTUAL_ENV" = "" ] ; then
	echo "ERROR: virtualenv (o alguno de la flia.) no encontrado"
	exit 1
fi

cd $(dirname $0)

export SKIP_SELENIUM=1
export FTS_DEBUG=1
export USE_PG=1
export FTS_SYSTEM_TEST=1

./deploy/docker-dev/run_integration_testing.sh &

python manage.py test fts_daemon.tests.st.test_system_test

kill %1
