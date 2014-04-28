# -*- coding: utf-8 -*-

'''
Created on Mar 31, 2014

@author: Horacio G. de Oro
'''

from __future__ import unicode_literals

from starpy import fastagi
from starpy.fastagi import FastAGIProtocol, FastAGIFactory
from twisted.internet import reactor
from twisted.web.client import Agent
from twisted.web.http_headers import Headers

# Import settings & models to force setup of Django
from django.conf import settings
from fts_web.models import Campana

import logging as _logging


# Seteamos nombre, sino al ser ejecutado via uWSGI
#  el logger se llamara '__main__'
logger = _logging.getLogger('fts_daemon.fastagi_daemon')


# FIXME: usar `SECRET_HEADER_NAME`!
SECRET_HEADER_NAME = 'FTSenderSecret'

# FIXME: usar `SECRET_HEADER_VALUE`!
SECRET_HEADER_VALUE = 'NosisFej2gighKag4Ong9Mypphip0GhovAn3Ez0'

# BIND = '172.19.1.104'
# TODO: mover a settings
BIND = '0.0.0.0'

# TODO: mover a settings
HTTP_SERVER = "http://localhost:8080"

# TODO: mover a settings
"""Url para registrar que se ha atendido la llamada"""
URL_REGISTRO_HA_ATENDIDO = "/_/agi/contesto/{0}/"


def fastagi_handler(agi):
    logger.debug('Iniciando ejecucion de handler...')
    assert isinstance(agi, FastAGIProtocol)
    agi_network_script = agi.variables.get('agi_network_script', '')
    # {fts_campana_id}/${{FtsDaemonCallId}}/opcion/{fts_opcion_id}/repetir/
    splitted = agi_network_script.split('/')
    if len(splitted) >= 4 and splitted[2] == 'opcion':
        logger.info('Request AGI: %s // campana: %s - call id: %s - opcion: %s',
            agi_network_script, splitted[0], splitted[1], splitted[3])
    else:
        logger.info('Request AGI: %s', agi_network_script)
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
                logger.info("Respusta HTTP recibida")

            d.addCallback(cbResponse)

    agi.finish()


def main():
    logger.info("Iniciando...")

    type(settings)  # hack to ignore pep8
    type(Campana)  # hack to ignore pep8

    fast_agi_server = fastagi.FastAGIFactory(fastagi_handler)
    assert isinstance(fast_agi_server, FastAGIFactory)
    reactor.listenTCP(4573, fast_agi_server, 50,  # @UndefinedVariable
        BIND)
    logger.info("Lanzando 'reactor.run()'")
    reactor.run()  # @UndefinedVariable

if __name__ == '__main__':
    main()
