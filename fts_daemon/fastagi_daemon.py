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

URL = settings.FTS_FAST_AGI_DAEMON_PROXY_URL + "/_/agi-proxy/{0}"


def fastagi_handler(agi):
    logger.debug('Iniciando ejecucion de handler...')
    assert isinstance(agi, FastAGIProtocol)

    agi_network_script = agi.variables.get('agi_network_script', '')
    url = URL.format(agi_network_script)
    logger.info('Request AGI: %s -> %s', agi_network_script, url)

    if not agi_network_script:
        logger.error("Se ha recibido 'agi_network_script' vacio")
        agi.finish()
        return

    agent = Agent(reactor)
    header = Headers({
        'FTSenderSecret': [settings.SECRET_KEY]
    })

    def cbResponse(ignored):
        logger.debug("Respuesta de servidor HTTP recibida")

    d = agent.request('GET', url, header, None)
    # d.addBoth(informar_ha_atendido)
    d.addCallback(cbResponse)


def main():
    logger.info("Iniciando...")

    type(settings)  # hack to ignore pep8
    type(Campana)  # hack to ignore pep8

    fast_agi_server = fastagi.FastAGIFactory(fastagi_handler)
    assert isinstance(fast_agi_server, FastAGIFactory)
    reactor.listenTCP(4573, fast_agi_server, 50,  # @UndefinedVariable
        settings.FTS_FAST_AGI_DAEMON_BIND)
    logger.info("Lanzando 'reactor.run()'")
    reactor.run()  # @UndefinedVariable

if __name__ == '__main__':
    main()
