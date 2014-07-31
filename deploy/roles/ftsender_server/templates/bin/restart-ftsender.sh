#!/bin/bash

# Reload de uWSGI
service ftsender-daemon reload

# FastAGI daemon -> NO LO BAJAMOS!
# fts-fastagi-daemon

# fts-llamador-poll-daemon
timeout 2s supervisorctl stop  fts-llamador-poll-daemon > /dev/null 2> /dev/null
timeout 5s supervisorctl start fts-llamador-poll-daemon > /dev/null 2> /dev/null

# fts-chequeador-campanas-vencidas
timeout 2s supervisorctl stop  fts-chequeador-campanas-vencidas > /dev/null 2> /dev/null
timeout 5s supervisorctl start fts-chequeador-campanas-vencidas > /dev/null 2> /dev/null

# fts-celery-worker-finalizar-campana
test -e /home/ftsender/deploy/run/celery-finalizar-campana.pid && pkill -SIGTERM -u ftsender -P $(cat /home/ftsender/deploy/run/celery-finalizar-campana.pid)

# fts-celery-worker-esperar-finaliza-campana
test -e /home/ftsender/deploy/run/celery-esperar-finaliza-campana.pid && pkill -SIGTERM -u ftsender -P $(cat /home/ftsender/deploy/run/celery-esperar-finaliza-campana.pid)

