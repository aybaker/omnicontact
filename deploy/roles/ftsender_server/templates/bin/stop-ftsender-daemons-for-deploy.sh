#!/bin/bash

#
# Este script funcionara aun cuando sea usado en el 1er deploy,
# ya que se usa solo: timeout, supervisorctl, y netstat,
# y no chequeamos exit status ;-)
#

# TODO: asegurarnos que fts-celery-worker-esperar-finaliza-campana esta bajado -> usar lock!

##------------------------------------------------------------
## Antes que nada le decimos a Celery workers que dejen
##  de realizar trabajos
##------------------------------------------------------------

# TODO - TODO - TODO - TODO - TODO - TODO - TODO - TODO

##------------------------------------------------------------
## Daemon Llamador
##------------------------------------------------------------

echo "Haciendo stop de 'fts-llamador-poll-daemon'"
timeout 2s supervisorctl stop fts-llamador-poll-daemon > /dev/null 2> /dev/null

while /bin/true ; do
    netstat -n | grep -q @freetechsender/daemon-llamador
    if [ $? -eq 1 ] ; then
        break
    else
		echo "Esperando stop de Daemon Llamador"
		sleep 1
    fi
done

##------------------------------------------------------------
## Chequeador campanas vencidas
##------------------------------------------------------------

echo "Haciendo stop de 'fts-chequeador-campanas-vencidas'"
timeout 2s supervisorctl stop  fts-chequeador-campanas-vencidas > /dev/null 2> /dev/null

while /bin/true ; do
    netstat -n | grep -q @freetechsender/daemon-finalizador-vencidas
    if [ $? -eq 1 ] ; then
        break
    else
		echo "Esperando stop de Daemon Chequeador de campanas vencidas"
		sleep 1
    fi
done

##------------------------------------------------------------
## Bajamos workers de Celery: esperar finaliza campana
##------------------------------------------------------------

# Esto hace que Supervisor baje los workers, pero cualquier
#  proceso hijo que este siendo ejecutado, continuara su ejecucion
echo "Haciendo stop de 'fts-celery-worker-esperar-finaliza-campana'"
timeout 2s supervisorctl stop fts-celery-worker-esperar-finaliza-campana > /dev/null 2> /dev/null

echo "Haciendo stop de 'fts-celery-worker-finalizar-campana'"
timeout 2s supervisorctl stop fts-celery-worker-finalizar-campana > /dev/null 2> /dev/null

while /bin/true ; do
    netstat -n | grep -q @freetechsender/depurador-de-campana
    if [ $? -eq 1 ] ; then
        break
    else
		echo "Esperando stop de worker Celery depurador de campanas"
		sleep 1
    fi
done
