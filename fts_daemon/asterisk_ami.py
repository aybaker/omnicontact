# -*- coding: utf-8 -*-
'''
Created on Mar 27, 2014

@author: Horacio G. de Oro
'''

from __future__ import unicode_literals

import logging as _logging
from multiprocessing import Process
from twisted.internet import reactor

from starpy import manager
from starpy.error import AMICommandFailure

from fts_web.settings import FTS_JOIN_TIMEOUT_MARGIN
import sys
import time


# `JOIN_TIMEOUT_MARGIN` lo importamos directamente, justamente para evitar
# importar nada de Django, ya que NO usamos nada de Django aqui

logger = _logging.getLogger('FTSAsteriskAmi')

ORIGINATE_RESULT_UNKNOWN = 59
ORIGINATE_RESULT_SUCCESS = 58
ORIGINATE_RESULT_FAILED = 57


def _get_result(exitstatus):
    if exitstatus == ORIGINATE_RESULT_UNKNOWN:
        return "ORIGINATE_RESULT_UNKNOWN"
    if exitstatus == ORIGINATE_RESULT_SUCCESS:
        return "ORIGINATE_RESULT_SUCCESS"
    if exitstatus == ORIGINATE_RESULT_FAILED:
        return "ORIGINATE_RESULT_FAILED"
    return "desconocido"


def _ami_login(username, password, server, port):
    """Logins to Asterisk AMI.
    Returns: AMI protocol instance
    """
    factory = manager.AMIFactory(username, password)
    ami_protocol = factory.login(server, port)
    return ami_protocol


class OriginateService(Process):
    """Genera ORIGINATEs usando AMI"""

    def __init__(self, username, password, server, port, channel, context,
        exten, priority, timeout):
        """Constructor. Recibe todos los parametros necesarios"""

        super(OriginateService, self).__init__()

        # Instancia de AMIProtocol
        self.ami = None
        self.originate_success = ORIGINATE_RESULT_UNKNOWN

        self.username = username
        self.password = password
        self.server = server
        self.port = port
        self.channel = channel
        self.context = context
        self.exten = exten
        self.priority = priority
        self.timeout = timeout

    def onResult(self, result):
        logger.debug("onResult(): result: %s", result)
        logger.debug("onResult(): type(result): %s", type(result))

        assert self.originate_success == ORIGINATE_RESULT_UNKNOWN
        try:
            if result['response'] == 'Success':
                self.originate_success = ORIGINATE_RESULT_SUCCESS
        except:
            pass

        if self.originate_success != ORIGINATE_RESULT_SUCCESS:
            logger.info("onResult() - Unknown result: %s", result)
            logger.info("onResult(): type(result): %s", type(result))

        logger.debug("onResult(): logging off")
        return self.ami.logoff()

    def onError(self, reason):
        logger.info("onError()")
        self.originate_success = ORIGINATE_RESULT_FAILED

        # reason -> twisted.python.failure.Failure
        # reason.value: {
        #    'message': 'Originate failed',
        #    'response': 'Error',
        #    'actionid': 'fx8120-52095600-2'}

        if isinstance(reason.value, AMICommandFailure):
            logger.info("onError(): AMICommandFailure(): %s", reason.value)
            return reason

        logger.info("---------- <onError()> -------------------------")
        logger.info("onError(): reason: %s", reason)
        logger.info("onError(): %s", reason.getTraceback())
        logger.info("---------- </onError()> -------------------------")
        return reason

    def onFinished(self, result):
        logger.info("onFinished(): Stopeando reactor...")
        reactor.stop()  # @UndefinedVariable

    def onConnect(self, ami):
        logger.info("onConnect()")

        #    logger.info("SE ESPERARAN 5 SEGUNDOS")
        #    import time
        #    time.sleep(5)
        #    logger.info("COOOONTINUAMOS....")

        # AMIProtocol.originate(
        #    self, channel, context=None, exten=None, priority=None,
        #    timeout=None, callerid=None, account=None, application=None,
        #    data=None, variable={}, async=False, channelid=None,
        #    otherchannelid=None
        # )
        assert self.ami is None
        self.ami = ami
        try:
            df = ami.originate(self.channel,
                context=self.context, exten=self.exten, priority=self.priority,
                timeout=self.timeout)
            df.addCallbacks(self.onResult, self.onError)
            df.addCallbacks(self.onFinished, self.onFinished)
            return df
        except:
            logger.exception("onConnect()")

    def _login_and_originate(self):
        logger.info("_login_and_originate()")
        try:
            assert self.ami is None
            #
            # Aca *NO* seteamos 'self.ami', ya que es un Deferred.
            # Lo seteamos en onConnect()
            #
            ami = _ami_login(self.username, self.password,
                self.server, self.port)
            ami.addCallback(self.onConnect)
        except:
            logger.exception("_login_and_originate")

    def run(self):
        """Metodo ejecutado en subproceso"""
        reactor.callWhenRunning(# @UndefinedVariable
            self._login_and_originate)
        logger.info("Iniciando reactor en subproceso %s", self.pid)
        reactor.run(installSignalHandlers=0)  # @UndefinedVariable
        logger.info("Reactor ha finalizado en subproceso %s", self.pid)
        sys.exit(self.originate_success)


#def originate_async(username, password, server, port,
#    outgoing_channel, context, exten, priority, timeout):
#    """Origina una llamada, en un subproceso separado.
#
#    Returns: subproceso ya arrancado
#    """
#    child_process = OriginateService(username, password, server, port,
#        outgoing_channel, context, exten, priority, timeout)
#    child_process.start()
#    return child_process


def originate(username, password, server, port,
    outgoing_channel, context, exten, priority, timeout):
    """Origina una llamada, en un subproceso separado.
    Espera a que se finalice la ejecucion. Por lo tanto, bloqueara,
    hasta que Asterisk devuelva OCUPADO, o que el destinatario
    ha respondido.
    """
    child_process = OriginateService(username, password, server, port,
        outgoing_channel, context, exten, priority, timeout)
    logger.info("Ejecutando ORIGINATE en subproceso")
    child_process.start()
    logger.info("Ejecutando join() en subproceso %s", child_process.pid)
    join_timeout = timeout + FTS_JOIN_TIMEOUT_MARGIN
    child_process.join(join_timeout)
    if child_process.is_alive():
        logger.warn("El subproceso %s NO ha devuelto el control"
            " despues de %s segundos. El proceso sera terminado.",
            child_process.pid, join_timeout)
        child_process.terminate()
        for _ in range(0, 20):
            if child_process.exitcode is not None:
                break
            time.sleep(0.1)
        if child_process.exitcode is None:
            logger.warn("No se consiguio 'exitcode' luego de 1 segundo")
    logger.info("El subproceso %s ha devuelto el control "
        "con exit code %s (%s)", child_process.pid, child_process.exitcode,
        _get_result(child_process.exitcode))
