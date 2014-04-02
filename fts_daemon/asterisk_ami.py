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


logger = _logging.getLogger('FTSAsteriskAmi')


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
        try:
            logger.info("onResult() -> Login OK - 'ORIGINATE' OK")
            for line in result:
                logger.info("originate> %s", line)
            return self.ami.logoff()
        except:
            logger.exception("onResult")

    def onError(self, reason):
        try:
            logger.error("onError() -> %s", reason.getTraceback())
            return reason
        except:
            logger.exception("onError")

    def onFinished(self, result):
        try:
            logger.info("onFinished() -> Stopeando reactor...")
            reactor.stop()  # @UndefinedVariable
        except:
            logger.exception("onFinished")

    def onConnect(self, ami):
        # AMIProtocol.originate(
        #    self, channel, context=None, exten=None, priority=None,
        #    timeout=None, callerid=None, account=None, application=None,
        #    data=None, variable={}, async=False, channelid=None,
        #    otherchannelid=None
        # )
        assert self.ami is None
        self.ami = ami
        try:
            logger.info("onConnect()")
            logger.info("Conectado!")
            df = ami.originate(self.channel,
                context=self.context, exten=self.exten, priority=self.priority,
                timeout=self.timeout)
            df.addCallbacks(self.onResult, self.onError)
            df.addCallbacks(self.onFinished, self.onFinished)
            return df
        except:
            logger.exception("onConnect")

    def _login_and_originate(self):
        try:
            assert self.ami is None
            logger.info("_login_and_originate()")
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


def originate_async(username, password, server, port,
    outgoing_channel, context, exten, priority, timeout):
    """Origina una llamada, en un subproceso separado.

    Returns: subproceso ya arrancado
    """
    child_process = OriginateService(username, password, server, port,
        outgoing_channel, context, exten, priority, timeout)
    child_process.start()
    return child_process


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
    child_process.join(timeout + 5)
    if child_process.is_alive():
        logger.warn("El subproceso %s ha devuelto el control"
            " despues de %s segundos. El proceso sera terminado.",
            child_process.pid, timeout)
        child_process.terminate()
    logger.info("El subproceso %s ha devuelto el control", child_process.pid)
