#!/bin/bash

/home/ftsender/deploy/virtualenv/bin/uwsgi \
    --module=fts_web.wsgi:application \
    --env DJANGO_SETTINGS_MODULE=fts_web.settings \
    --master \
    --processes=5 \
    --enable-threads \
    --home=/home/ftsender/deploy/virtualenv \
    --http=0.0.0.0:8080 \
    --python-path=/home/ftsender/deploy/app \
    --python-path=/home/ftsender/deploy/local \
    --static-map /static=${BASEDIR_WEB}/fts_web/static \
    --mule=/home/ftsender/deploy/app/fts_daemon/poll_daemon/main.py \
    --mule=/home/ftsender/deploy/app/fts_daemon/fastagi_daemon.py \
    --pidfile /home/ftsender/deploy/run/fts-uwsgi.pid \
    --die-on-term \
    --master-fifo /home/ftsender/deploy/run/.uwsgi-fifo \
    $*
