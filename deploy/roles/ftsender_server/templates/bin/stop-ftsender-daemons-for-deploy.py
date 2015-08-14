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
import logging.handlers
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


def bajar_uwsgi():
    logger.info("# ------------------------------------------------------------------------------------------")
    logger.info("# Bajamos uWSGI")
    logger.info("# ------------------------------------------------------------------------------------------")

    # TOMAR PID (si existe)
    # /home/ftsender/deploy/run/fts-uwsgi.pid
    if os.path.exists(UWSGI_PID_FILE):
        with open(UWSGI_PID_FILE, 'r') as pid_file:
            uwsgi_pid = pid_file.read().splitlines()[0]
    else:
        uwsgi_pid = None

    logger.info(" + uWSGI pid: %s", uwsgi_pid)

    if uwsgi_pid:
        try:
            shell("pgrep -u ftsender uwsgi | egrep -q '^{0}$'".format(uwsgi_pid))
        except subprocess.CalledProcessError:
            pass
        else:
            logger.info(" + Bajando servicio 'ftsender-daemon'")
            try:
                shell("/sbin/service ftsender-daemon stop")
            except subprocess.CalledProcessError:
                logger.exception("ERROR DETECTADO al intentar bajar servicio 'ftsender-daemon'")


def main():

    if 'DEBUG' in os.environ:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.INFO)

    handler = logging.handlers.SysLogHandler(address=str('/dev/log'))
    logging.getLogger('').addHandler(handler)

    bajar_uwsgi()

    logger.info("# ------------------------------------------------------------------------------------------")
    logger.info("# Antes que nada pedimos a Supervisor q' baje tasks")
    logger.info("# ------------------------------------------------------------------------------------------")

    for task in SUPERVISORD_SUBPROCESSES:
        logger.info("Bajando subprocess %s", task)
        try:
            shell("/usr/bin/timeout 2s supervisorctl stop {0} > /dev/null 2> /dev/null".format(task))
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
                    shell("/usr/bin/timeout 2s supervisorctl stop {0} > /dev/null 2> /dev/null".format(task))
                time.sleep(1)

            logger.error("Despues de 60 segundos, no se encontro el subproceso '%s' en estado STOPPED!", task)
            _, stdout, stderr = get_output("/usr/bin/timeout 5s supervisorctl status")
            logger.error(" + supervisorctl status - STDOUT")
            logger.error("%s", stdout)
            logger.error(" + supervisorctl status - STDERR")
            logger.error("%s", stderr)
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
            for iter_num in range(int(180)):
                if iter_num % 5 == 0:
                    shell("netstat -n | grep -q '{0}'".format(lock_name))
                    logger.info(" + Lock '%s' EXISTE, esperaremos y re-chequearemos...", lock_name)
                    time.sleep(5)

            # El lock existe despues de esperar bastante. Salimos con error
            logger.error("Despues de esperar un tiempo, el lock '%s' no ha sido liberado", lock_name)
            _, stdout, stderr = get_output("netstat -nx | grep @")
            logger.error(" + netstat - STDOUT")
            logger.error("%s", stdout)
            logger.error(" + netstat - STDERR")
            logger.error("%s", stderr)
            sys.exit(1)

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

    logger.info("# ------------------------------------------------------------------------------------------")
    logger.info("# FIN!")
    logger.info("# ------------------------------------------------------------------------------------------")


if __name__ == '__main__':
    main()
