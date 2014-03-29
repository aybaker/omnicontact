# -*- coding: utf-8 -*-
'''
Created on Mar 27, 2014

@author: Horacio G. de Oro
'''

from __future__ import unicode_literals

import logging
from threading import Thread
from twisted.internet import reactor

from starpy import manager


logger = logging.getLogger('FTSAsteriskAmi')


def _ami_login(username, password, server, port):
    """Logins to Asterisk AMI.
    Returns: AMI protocol instance
    """
    factory = manager.AMIFactory(username, password)
    ami_protocol = factory.login(server, port)
    return ami_protocol


class OriginateInThread(Thread):
    """Thread que realiza ORIGINATE usando AMI"""

    def __init__(self, username, password, server, port, channel, context,
        exten, priority, timeout):
        """Constructor. Recibe todos los parametros necesarios"""

        super(OriginateInThread, self).__init__()

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
            self.ami = _ami_login(self.username, self.password, self.server,
                self.port)
            self.ami.addCallback(self.onConnect)
        except:
            logger.exception("_login_and_originate")

    def run(self):
        """Metodo ejecutado en thread"""
        reactor.callWhenRunning(# @UndefinedVariable
            self._login_and_originate)
        logger.info("[%s] Iniciando reactor...")
        reactor.run(installSignalHandlers=0)  # @UndefinedVariable
        logger.info("[%s] Reactor ha finalizado")


def originate_async(username, password, server, port,
    outgoing_channel, context, exten, priority, timeout):
    """Origina una llamada, en un thread separado.

    Returns: thread ya arrancado
    """
    thread = OriginateInThread(username, password, server, port,
        outgoing_channel, context, exten, priority, timeout)
    thread.start()
    return thread


def originate(username, password, server, port,
    outgoing_channel, context, exten, priority, timeout):
    """Origina una llamada, en un thread separado.
    Espera a que se finalice la ejecucion
    """
    thread = OriginateInThread(username, password, server, port,
        outgoing_channel, context, exten, priority, timeout)
    logging.info("Ejecutando ORIGINATE en thread %s", thread.ident)
    thread.start()
    logging.info("Ejecutando join() en thread %s", thread.ident)
    thread.join()
    logging.info("El thread %s ha devuelto el control")
