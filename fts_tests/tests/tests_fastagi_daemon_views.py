# -*- coding: utf-8 -*-

"""Tests generales"""
from __future__ import unicode_literals

import logging

from django.db import connection
from django.utils.unittest.case import skipUnless
from fts_daemon.fastagi_daemon_views import create_urls, create_regex, \
    fin_err_t, get_view, insert_evento_de_contacto, UrlNoMatcheaNingunaVista
from fts_daemon.models import EventoDeContacto
from fts_web.tests.utiles import \
    FTSenderBaseTest, default_db_is_postgresql


#from django.conf import settings
logger = logging.getLogger(__name__)


#==============================================================================
# Mocks
#==============================================================================

class DjCursorMock(object):
    """Mock de cursor"""

    def __init__(self, cursor):
        self._cursor = cursor

    def execute(self, *args, **kwargs):
        return self._cursor.execute(*args, **kwargs)


class DjConnectionMock(object):
    """Mock de connection"""

    def __init__(self):
        self.autocommit = True

    def cursor(self):
        return DjCursorMock(connection.cursor())


class DjConnectionPoolMock(object):
    """Mock de connection pool de psycopg2"""

    def getconn(self):
        return DjConnectionMock()

    def putconn(self, conn):
        pass


#==============================================================================
# Tests
#==============================================================================

class FastAgiViewsTests(FTSenderBaseTest):

    def test_create_urls_returns_without_error(self):
        urls = create_urls()
        self.assertTrue(len(urls) > 0)

    def test_create_regex_returns_without_error(self):
        regexes = create_regex()
        self.assertTrue(len(regexes) > 0)

    def test_get_view_falla_con_url_invalido(self):
        regexes = create_regex()

        with self.assertRaises(UrlNoMatcheaNingunaVista):
            get_view(regexes, ' ')

        with self.assertRaises(UrlNoMatcheaNingunaVista):
            get_view(regexes, '/')

        with self.assertRaises(UrlNoMatcheaNingunaVista):
            get_view(regexes, ' ')

        with self.assertRaises(UrlNoMatcheaNingunaVista):
            get_view(regexes, '1')

        with self.assertRaises(UrlNoMatcheaNingunaVista):
            get_view(regexes, '1/2')

        with self.assertRaises(UrlNoMatcheaNingunaVista):
            get_view(regexes, '1/2/3')

        with self.assertRaises(UrlNoMatcheaNingunaVista):
            get_view(regexes, '1/2/3/')

        with self.assertRaises(UrlNoMatcheaNingunaVista):
            get_view(regexes, '1/2/3/4')

        with self.assertRaises(UrlNoMatcheaNingunaVista):
            get_view(regexes, '1/2/3/4/')

    def test_get_view_devuelve_view_err_t(self):
        #'^(?P<campana_id>\d+)/(?P<contacto_id>\d+)/(?P<intento>\d+)'
        #    '/fin_err_t/$',
        #fin_err_t))

        campana_id = "1"
        contacto_id = "2"
        intento = "3"
        func = fin_err_t

        url = "{0}/{1}/{2}/fin_err_t/".format(
            campana_id, contacto_id, intento)

        regexes = create_regex()

        # -----
        view, kwargs = get_view(regexes, url)

        self.assertEqual(view, func)
        self.assertEquals(kwargs, {
            'campana_id': campana_id,
            'contacto_id': contacto_id,
            'intento': intento,
        })

    @skipUnless(default_db_is_postgresql(), "Requiere PostgreSql")
    def test_insert_evento_de_contacto_inserta_datos(self):
        CONN_POOL = DjConnectionPoolMock()

        campana = self.crear_campana_activa(cant_contactos=2,
            cantidad_canales=1)
        campana_id = str(campana.id)
        contacto_id = str(campana.bd_contacto.contactos.all()[0].id)

        self.assertEqual(EventoDeContacto.objects.count(), 2)

        insert_evento_de_contacto(CONN_POOL, campana_id, contacto_id, 3, 4)
