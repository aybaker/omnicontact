#!/bin/bash

# Reload de uWSGI
service ftsender-daemon reload

# fts-celery-worker-finalizar-campana
test -e /home/ftsender/deploy/run/celery-finalizar-campana.pid && pkill -SIGTERM -u ftsender -P $(cat /home/ftsender/deploy/run/celery-finalizar-campana.pid)

# fts-celery-worker-esperar-finaliza-campana
test -e /home/ftsender/deploy/run/celery-esperar-finaliza-campana.pid && pkill -SIGTERM -u ftsender -P $(cat /home/ftsender/deploy/run/celery-esperar-finaliza-campana.pid)

# FastAGI daemon -> NO LO BAJAMOS!
# fts-fastagi-daemon

# fts-llamador-poll-daemon
timeout 2s supervisorctl stop  fts-llamador-poll-daemon > /dev/null 2> /dev/null
timeout 5s supervisorctl start fts-llamador-poll-daemon > /dev/null 2> /dev/null

# fts-chequeador-campanas-vencidas
timeout 2s supervisorctl stop  fts-chequeador-campanas-vencidas > /dev/null 2> /dev/null
timeout 5s supervisorctl start fts-chequeador-campanas-vencidas > /dev/null 2> /dev/null

pgrep -u ftsender -f /home/ftsender/deploy/virtualenv/bin/uwsgi                                      > /dev/null || { echo "ERROR: parece que uWSGI no esta corriendo"; exit 1; }
pgrep -u ftsender -f /home/ftsender/deploy/app/fts_daemon/poll_daemon/main.py                        > /dev/null || { echo "ERROR: parece que daemon llamador no esta corriendo"; exit 1; }
pgrep -u ftsender -f /home/ftsender/deploy/app/fts_daemon/services/finalizador_vencidas_daemon.py    > /dev/null || { echo "ERROR: parece que daemon finalizador de campanas no esta corriendo"; exit 1; }
pgrep -u ftsender -f queues=esperar_y_finalizar_campana                                              > /dev/null || { echo "ERROR: parece que worker Celery 'esperar_y_finalizar_campana' no esta corriendo"; exit 1; }
pgrep -u ftsender -f queues=finalizar_campana                                                        > /dev/null || { echo "ERROR: parece que worker Celery 'finaliza_campana' no esta corriendo"; exit 1; }
