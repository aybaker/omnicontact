# -*- coding: utf-8 -*-

"""
Este script es ejecutado en el servidor (por eso no podemos importar ninguna constante!)
y la funcion que tiene es subir los servicios despues de haber realizado el deploy.

Inicia los sigientes servicos:
    - uWSGI (servidor Django)

Inicia los siguientes subprocesos de Supervisor:
    - fts-llamador-poll-daemon
    - fts-chequeador-campanas-vencidas
    - fts-celery-worker-esperar-finaliza-campana
    - fts-celery-worker-finalizar-campana

"""

from __future__ import unicode_literals

import logging
import logging.handlers
import os
import subprocess
import sys
import time

logger = logging.getLogger('start-ftpsender')

#
# 8< --- copy & paste --- Mantener esto igual al script de START --- >8
#

SUPERVISORD_SUBPROCESSES = [
    "fts-llamador-poll-daemon",
    "fts-chequeador-campanas-vencidas",
    "fts-celery-worker-esperar-finaliza-campana",
    "fts-celery-worker-finalizar-campana",
]

# Usamos mismo nombre de variables q' en codigo, y agregamos '@'
LOCK_DAEMON_LLAMADOR = '@freetechsender/daemon-llamador'
LOCK_DAEMON_FINALIZADOR_VENCIDAS = '@freetechsender/daemon-finalizador-vencidas'
LOCK_ESPERADOR_FINALIZACION_DE_LLAMADAS = '@freetechsender/esperador-finalizacion-de-llamadas'
# LOCK_ESPERADOR_FINALIZACION_DE_LLAMADAS: el lock se llamara XXX-0, XXX-1, etc., pero no hay
#  problema, porque hacemos el grep funcionara igual sin importar el sufijo
LOCK_DEPURACION_DE_CAMPANA = '@freetechsender/depurador-de-campana'

LOCK_SOCKETS = [
    LOCK_DAEMON_LLAMADOR,
    LOCK_DAEMON_FINALIZADOR_VENCIDAS,
    LOCK_ESPERADOR_FINALIZACION_DE_LLAMADAS,
    LOCK_DEPURACION_DE_CAMPANA,
]

UWSGI_PID_FILE = "/home/ftsender/deploy/run/fts-uwsgi.pid"


def shell(cmd):
    """Ejecuta comando shell, lanza excepcion si exit status != 0"""
    logger.debug(" + Ejecutando '%s'", cmd)
    subprocess.check_call(cmd, shell=True)


def get_output(cmd, stderr=subprocess.PIPE):
    """Ejecuta comando shell, devuelve [proc, stdout, stderr]"""
    proc = subprocess.Popen(
        cmd,
        shell=True,
        stdout=subprocess.PIPE,
        stderr=stderr,
    )
    stdout, stderr = proc.communicate()
    return proc, stdout, stderr


def setup_logging():
    if 'DEBUG' in os.environ:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.INFO)

    handler = logging.handlers.SysLogHandler(address=str('/dev/log'))
    logging.getLogger('').addHandler(handler)


class Done(Exception):
    pass

#
# 8< (FIN) --- copy & paste --- Mantener esto igual al script de STOP --- >8
#


def iniciar_uwsgi():
    logger.info("# ------------------------------------------------------------------------------------------")
    logger.info("# Iniciamos uWSGI")
    logger.info("# ------------------------------------------------------------------------------------------")

    logger.info(" + Iniciando servicio 'ftsender-daemon'")
    try:
        shell("/sbin/service ftsender-daemon start")
    except subprocess.CalledProcessError:
        logger.exception("ERROR DETECTADO al intentar iniciar servicio 'ftsender-daemon'")


def main():
    setup_logging()
    iniciar_uwsgi()

    logger.info("# ------------------------------------------------------------------------------------------")
    logger.info("# Antes que nada pedimos a Supervisor q' inicie subprocesos")
    logger.info("# ------------------------------------------------------------------------------------------")

    for task in SUPERVISORD_SUBPROCESSES:
        logger.info("Iniciando subprocess %s", task)
        try:
            shell("/usr/bin/timeout 2s supervisorctl start {0} > /dev/null 2> /dev/null".format(task))
        except subprocess.CalledProcessError:
            pass

    logger.info("# ------------------------------------------------------------------------------------------")
    logger.info("# Chequeamos status de subprocesos de supervisord")
    logger.info("# ------------------------------------------------------------------------------------------")

    # Inicialmente los subprocesos estan en estado STARTING, durante unos segundos,
    #  luego pasan a 'RUNNING'

    for task in SUPERVISORD_SUBPROCESSES:
        logger.info("Chequeando si %s esta en estado RUNNING", task)
        try:
            for iter_num in range(1, 31):
                try:
                    shell("supervisorctl status | egrep '^{0}' | grep -q RUNNING".format(task))
                    raise Done()
                except subprocess.CalledProcessError:
                    time.sleep(1)

            logger.error("Despues de 30 segundos, no se encontro el subproceso '%s' en estado RUNNING!", task)
            _, stdout, stderr = get_output("/usr/bin/timeout 5s supervisorctl status")
            logger.error(" + supervisorctl status - STDOUT")
            logger.error("%s", stdout)
            logger.error(" + supervisorctl status - STDERR")
            logger.error("%s", stderr)
            sys.exit(1)

        except Done:
            # Se encontro RUNNING, el subproceso ya esta andando
            logger.info(" + Supervisor: subproceso '%s' en stado RUNNING, continuamos...", task)

    logger.info("# ------------------------------------------------------------------------------------------")
    logger.info("# FIN!")
    logger.info("# ------------------------------------------------------------------------------------------")


if __name__ == '__main__':
    main()
