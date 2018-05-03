# -*- coding: utf-8 -*-

'''
Created on Mar 31, 2014

@author: Horacio G. de Oro
'''

from __future__ import unicode_literals

import logging as _logging

import django
from django.conf import settings

from psycopg2 import pool

from starpy import fastagi
from starpy.fastagi import FastAGIProtocol, FastAGIFactory

from twisted.internet import reactor
from twisted.python import log

try:
    # FIXME: Necesario para que se haga el import cuando se ejecutan los tests
    from fts_daemon import fastagi_daemon_views
    from fts_daemon.fastagi_daemon_views import UrlNoMatcheaNingunaVista
except:
    pass


# Import settings & models to force setup of Django
CONN_POOL = None

REGEX = None

INSERT_FUNCION = None

# Seteamos nombre, sino al ser ejecutado via uWSGI
#  el logger se llamara '__main__'
logger = _logging.getLogger('fts_daemon.fastagi_daemon')

# FIXME: eliminar `FTS_FAST_AGI_DAEMON_PROXY_URL`
# URL = settings.FTS_FAST_AGI_DAEMON_PROXY_URL + "/_/agi-proxy/{0}"


#==============================================================================
# Funciones varias
#==============================================================================

def do_insert(_reactor, _conn_pool, _regexes, agi_network_script):
    """Realiza insert de evento representado por agi_network_script
    recibido via AGI.

    Recibe todos los parametros para que sea facil de testear con mocks.
    
    :raises: UrlNoMatcheaNingunaVista
    """
    view, kwargs = fastagi_daemon_views.get_view(
        _regexes, agi_network_script)  # -> UrlNoMatcheaNingunaVista

    _reactor.callInThread(# @UndefinedVariable
        view, _conn_pool, **kwargs)


def setup_connection_pool():
    """Realiza setup de connection pool.

    Esto es un workaround. Quiza Twisted posea alguna manera de
    compartir el conn. pool de alguna manera mas elegante.

    No hace falta LOCKear porque esta funcion se llama desde
    el main(), ANTES de iniciar Twisted.
    """
    # TODO: investigar como se pueden mover todas estas variables
    #  globales a un objeto, o elminar las variables globales, de
    #  alguna manera compatible con Twisted
    global CONN_POOL
    port = settings.DATABASES['default'].get('PORT', None)
    CONN_POOL = pool.ThreadedConnectionPool(5, 20,
        database=settings.DATABASES['default']['NAME'],
        user=settings.DATABASES['default']['USER'],
        password=settings.DATABASES['default']['PASSWORD'],
        host=settings.DATABASES['default']['HOST'],
        port=port,
    )


def setup_globals():
    """Realiza setup de variables globales necesarias.

    Esto es un workaround. Quiza Twisted posea alguna manera de
    compartir estas variables de alguna manera mas elegante.

    No hace falta LOCKear porque esta funcion se llama desde
    el main(), ANTES de iniciar Twisted.
    """
    # TODO: investigar como se pueden mover todas estas variables
    #  globales a un objeto, o elminar las variables globales, de
    #  alguna manera compatible con Twisted

    # Setup regex
    global REGEX
    REGEX = fastagi_daemon_views.create_regex()

    global INSERT_FUNCION
    INSERT_FUNCION = do_insert


#==============================================================================
# Twisted / AGI
#==============================================================================

def fastagi_handler(agi):
    """Handler para requests AGI"""
    logger.debug('Iniciando ejecucion de handler...')
    assert isinstance(agi, FastAGIProtocol)

    agi_network_script = agi.variables.get('agi_network_script', '')
    logger.debug('agi_network_script: %s', agi_network_script)

    if agi_network_script:
        try:
            INSERT_FUNCION(reactor, CONN_POOL, REGEX, agi_network_script)
        except UrlNoMatcheaNingunaVista:
            logger.exception("El request recibido no se pudo procesar, "
                "ya que no hay vista asociada")
        except:
            logger.exception("El request recibido no se pudo procesar")
    else:
        logger.error("Se ha recibido 'agi_network_script' vacio")

    agi.finish()


def main():
    observer = log.PythonLoggingObserver()
    observer.start()

    logger.info("Iniciando...")

    setup_connection_pool()
    setup_globals()

    fast_agi_server = fastagi.FastAGIFactory(fastagi_handler)
    assert isinstance(fast_agi_server, FastAGIFactory)
    reactor.listenTCP(4573, fast_agi_server, 50,  # @UndefinedVariable
        settings.FTS_FAST_AGI_DAEMON_BIND)
    logger.info("Lanzando 'reactor.run()'")
    reactor.run()  # @UndefinedVariable

if __name__ == '__main__':
    django.setup()

    from fts_daemon import fastagi_daemon_views
    from fts_daemon.fastagi_daemon_views import UrlNoMatcheaNingunaVista

    main()
