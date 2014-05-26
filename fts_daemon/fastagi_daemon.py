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
from twisted.python import log

from psycopg2 import pool

CONN_POOL = None


# Seteamos nombre, sino al ser ejecutado via uWSGI
#  el logger se llamara '__main__'
logger = _logging.getLogger('fts_daemon.fastagi_daemon')

URL = settings.FTS_FAST_AGI_DAEMON_PROXY_URL + "/_/agi-proxy/{0}"


def fastagi_handler(agi):
    logger.debug('Iniciando ejecucion de handler...')
    assert isinstance(agi, FastAGIProtocol)

    agi_network_script = agi.variables.get('agi_network_script', '')
    reactor.callInThread(do_sql, agi_network_script)  # @UndefinedVariable

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

    agi.finish()


def do_sql(url):
    # print "--- do_sql() ---"
    # print "CONN_POOL: {0}".format(CONN_POOL)
    conn = None
    try:
        conn = CONN_POOL.getconn()
        if not conn.autocommit:
            conn.autocommit = True
        cur = conn.cursor()
        cur.execute("INSERT INTO urls (url) VALUES (%s)",
            [url])
    except:
        logger.exception("No se pudo insertar URL")
    finally:
        if conn is not None:
            CONN_POOL.putconn(conn)


def main():
    observer = log.PythonLoggingObserver()
    observer.start()

    logger.info("Iniciando...")

    type(settings)  # hack to ignore pep8
    type(Campana)  # hack to ignore pep8

    global CONN_POOL
    CONN_POOL = pool.ThreadedConnectionPool(5, 20,
        database=settings.DATABASES['default']['NAME'],
        user=settings.DATABASES['default']['USER'],
        password=settings.DATABASES['default']['PASSWORD']
    )

    fast_agi_server = fastagi.FastAGIFactory(fastagi_handler)
    assert isinstance(fast_agi_server, FastAGIFactory)
    reactor.listenTCP(4573, fast_agi_server, 50,  # @UndefinedVariable
        settings.FTS_FAST_AGI_DAEMON_BIND)
    logger.info("Lanzando 'reactor.run()'")
    reactor.callInThread(do_sql, 'twisted/iniciando/')  # @UndefinedVariable
    reactor.run()  # @UndefinedVariable

if __name__ == '__main__':
    main()
