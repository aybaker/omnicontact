# -*- coding: utf-8 -*-

'''
Created on Mar 31, 2014

@author: Horacio G. de Oro
'''

from __future__ import unicode_literals

from django.conf import settings
from fts_daemon import fastagi_daemon_views
import logging as _logging
from psycopg2 import pool
from starpy import fastagi
from starpy.fastagi import FastAGIProtocol, FastAGIFactory
from twisted.internet import reactor
from twisted.python import log


# Import settings & models to force setup of Django
CONN_POOL = None

REGEX = None

# Seteamos nombre, sino al ser ejecutado via uWSGI
#  el logger se llamara '__main__'
logger = _logging.getLogger('fts_daemon.fastagi_daemon')

# FIXME: eliminar `FTS_FAST_AGI_DAEMON_PROXY_URL`
# URL = settings.FTS_FAST_AGI_DAEMON_PROXY_URL + "/_/agi-proxy/{0}"


def fastagi_handler(agi):
    logger.debug('Iniciando ejecucion de handler...')
    assert isinstance(agi, FastAGIProtocol)

    agi_network_script = agi.variables.get('agi_network_script', '')
    logger.info('agi_network_script: %s', agi_network_script)
    if not agi_network_script:
        logger.error("Se ha recibido 'agi_network_script' vacio")
        agi.finish()
        return

    try:
        view, kwargs = fastagi_daemon_views.get_view(
            REGEX, agi_network_script)
    except:
        view, kwargs = None, None
        logger.exception("Error al buscar vista mapeada a url '%s'",
            agi_network_script)

    if view and kwargs:
        reactor.callInThread(# @UndefinedVariable
            view, CONN_POOL, **kwargs)

    agi.finish()


def setup_globals():
    # Setup connection pool
    global CONN_POOL
    CONN_POOL = pool.ThreadedConnectionPool(5, 20,
        database=settings.DATABASES['default']['NAME'],
        user=settings.DATABASES['default']['USER'],
        password=settings.DATABASES['default']['PASSWORD']
    )

    # Setup regex
    global REGEX
    REGEX = fastagi_daemon_views.create_regex()


def main():
    observer = log.PythonLoggingObserver()
    observer.start()

    logger.info("Iniciando...")

    setup_globals()

    fast_agi_server = fastagi.FastAGIFactory(fastagi_handler)
    assert isinstance(fast_agi_server, FastAGIFactory)
    reactor.listenTCP(4573, fast_agi_server, 50,  # @UndefinedVariable
        settings.FTS_FAST_AGI_DAEMON_BIND)
    logger.info("Lanzando 'reactor.run()'")
    reactor.run()  # @UndefinedVariable

if __name__ == '__main__':
    main()
