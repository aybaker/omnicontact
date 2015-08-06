# -*- coding: utf-8 -*-

"""

FIXME: chequear si anda en 1er deploy!
FIXME: chequear si anda en 1er deploy!
FIXME: chequear si anda en 1er deploy!
FIXME: chequear si anda en 1er deploy!
FIXME: chequear si anda en 1er deploy!
FIXME: chequear si anda en 1er deploy!
FIXME: chequear si anda en 1er deploy!
FIXME: chequear si anda en 1er deploy!
FIXME: chequear si anda en 1er deploy!
FIXME: chequear si anda en 1er deploy!
FIXME: chequear si anda en 1er deploy!
FIXME: chequear si anda en 1er deploy!
FIXME: chequear si anda en 1er deploy!
FIXME: chequear si anda en 1er deploy!
FIXME: chequear si anda en 1er deploy!
FIXME: chequear si anda en 1er deploy!
FIXME: chequear si anda en 1er deploy!
FIXME: chequear si anda en 1er deploy!
FIXME: chequear si anda en 1er deploy!
FIXME: chequear si anda en 1er deploy!

"""

from __future__ import unicode_literals

import logging
import os
import subprocess
import sys
import time

logger = logging.getLogger('main')

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


def shell(cmd):
    logger.debug(" + Ejecutando '%s'", cmd)
    subprocess.check_call(cmd, shell=True)


def main():

    if 'DEBUG' in os.environ:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.INFO)

    logger.info("# ------------------------------------------------------------------------------------------")
    logger.info("# Antes que nada pedimos a Supervisor q' baje tasks")
    logger.info("# ------------------------------------------------------------------------------------------")

    for task in SUPERVISORD_SUBPROCESSES:
        logger.info("Bajando subprocess %s", task)
        try:
            shell("/usr/bin/timeout 2s supervisorctl stop {0} > /dev/null 2> /dev/null")
        except subprocess.CalledProcessError:
            pass

    logger.info("# ------------------------------------------------------------------------------------------")
    logger.info("# Chequeamos supervisord status & reintentamos")
    logger.info("# ------------------------------------------------------------------------------------------")

    for task in SUPERVISORD_SUBPROCESSES:
        logger.info("Chequeando %s", task)
        try:
            for iter_num in range(1, 61):
                shell("supervisorctl status | egrep '^{0}' | grep -q -v STOPPED".format(task))
                if iter_num % 10 == 0:
                    shell("/usr/bin/timeout 2s supervisorctl stop {0} > /dev/null 2> /dev/null")
                time.sleep(1)

            logger.error("Despues de 60 segundos, no se encontro el subproceso '{0}' en estado STOPPED!")
            sys.exit(1)

        except subprocess.CalledProcessError:
            # Se encontro STOPPED, lo que implica que ya estamos seguros que
            # supervisord paso el subproceso a estado STOPPED
            logger.info(" + Supervisor: subproceso '%s' en stado STOPPED, continuamos...", task)

    logger.info("# ------------------------------------------------------------------------------------------")
    logger.info("# Chequeamos LOCK SOCKETS")
    logger.info("# ------------------------------------------------------------------------------------------")

    for lock_name in LOCK_SOCKETS:
        logger.info("Chequeando LOCK '%s'", lock_name)
        try:
            while shell("netstat -n | grep -q '{0}'".format(lock_name)):
                logger.info(" + Lock '%s' EXISTE, esperaremos y re-chequearemos...", lock_name)
                time.sleep(5)
        except subprocess.CalledProcessError:
            # No se encontro lock, podemos continuar
            logger.info(" + Lock '%s' no existe, continuamos...", lock_name)

    # --------------------------------------------------------------------------------------------------------------
    # A esta altura, podemos estar seguros que:
    #  1. los subprocesos de Supervisord estan en estado STOPPED
    #  2. no existen LOCKs (por lo tanto, suponemos q' los procesos reales tampoco estan andando)
    #     Esto es importante para los workers de Celery, ya que el worker puede estar stoppeado, pero
    #     el proceso 'forked' puede haber quedado andando, por eso el lock es importante. Esto, agregado a que
    #     los workers usan --maxtasksperchild=1, nos asegura que, al finalizar el trabajo, el proceso 'forked'
    #     se cerrara y no se volvera a ejecutar otra tarea
    # --------------------------------------------------------------------------------------------------------------

if __name__ == '__main__':
    main()
