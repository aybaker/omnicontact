# -*- coding: utf-8 -*-

'''
Created on Mar 31, 2014

@author: Horacio G. de Oro
'''

from __future__ import unicode_literals

import logging as _logging
from twisted.internet import reactor
from twisted.web.client import Agent
from twisted.web.http_headers import Headers

from starpy import fastagi
from starpy.fastagi import FastAGIProtocol, FastAGIFactory


logger = _logging.getLogger("FTSenderFastAgiDaemon")


def setup():
    from django.conf import settings  # @UnusedImport
    from fts_web.models import Campana  # @UnusedImport
    # _logging.getLogger().setLevel(_logging.INFO)


SECRET_HEADER_NAME = 'FTSenderSecret'
SECRET_HEADER_VALUE = 'NosisFej2gighKag4Ong9Mypphip0GhovAn3Ez0'

# BIND = '172.19.1.104'
BIND = '0.0.0.0'

HTTP_SERVER = "http://localhost:8080"

"""Url para registrar que se ha atendido la llamada"""
URL_REGISTRO_HA_ATENDIDO = "/_/agi/contesto/{0}/"


def fastagi_handler(agi):
    logger.info('Iniciando ejecucion de handler...')
    assert isinstance(agi, FastAGIProtocol)
    agi_network_script = agi.variables.get('agi_network_script', '')
    splitted = agi_network_script.split('/')
    if len(splitted) == 2:
        if splitted[1] == 'ha-contestado':
            id_intento = splitted[0]
            logger.info("Ha contestado: %s", id_intento)
            agent = Agent(reactor)
            header = Headers({
                SECRET_HEADER_NAME: [SECRET_HEADER_VALUE]
            })
            url = HTTP_SERVER + URL_REGISTRO_HA_ATENDIDO.format(
                id_intento)
            d = agent.request('GET', url, header, None)
            # d.addBoth(informar_ha_atendido)

            def cbResponse(ignored):
                print '>>>>>>>>>> Response received'

            d.addCallback(cbResponse)

    agi.finish()


if __name__ == '__main__':
    _logging.basicConfig(level=_logging.INFO)
    logger.info("Iniciando...")
    setup()

    logger.info("Setup de Django OK")

    fast_agi_server = fastagi.FastAGIFactory(fastagi_handler)
    assert isinstance(fast_agi_server, FastAGIFactory)
    reactor.listenTCP(4573, fast_agi_server, 50,  # @UndefinedVariable
        BIND)
    logger.info("Lanzando 'reactor.run()'")
    reactor.run()  # @UndefinedVariable
