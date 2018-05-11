# -*- coding: utf-8 -*-

"""Tests generales"""
from __future__ import unicode_literals

import logging

from fts_daemon import fastagi_daemon
from fts_daemon.fastagi_daemon_views import create_regex, \
    UrlNoMatcheaNingunaVista
from fts_tests.tests import tests_fastagi_daemon_views
from fts_web.tests.utiles import FTSenderBaseTest
from starpy.fastagi import FastAGIProtocol
import mock
from fts_daemon.models import EventoDeContacto


#from django.conf import settings
logger = logging.getLogger(__name__)


#==============================================================================
# Mocks
#==============================================================================

class TwistedReactorMock(object):

    def callInThread(self, func_to_call, *args, **kwargs):
        func_to_call(*args, **kwargs)


def do_insert_mock(_reactor, _conn_pool, _regexes, agi_network_script):
    return fastagi_daemon.do_insert(
        TwistedReactorMock(),
        tests_fastagi_daemon_views.DjConnectionPoolMock(),
        fastagi_daemon.REGEX,
        agi_network_script
    )


#==============================================================================
# Tests
#==============================================================================

class FastAgiTests(FTSenderBaseTest):

    def test_fastagi_handler_realiza_insert_de_url_valida(self):
        # FIXME: implementar test usando Twisted

        campana = self.crear_campana_activa(cant_contactos=2,
            cantidad_canales=1)
        campana_id = str(campana.id)
        contacto_id = str(campana.bd_contacto.contactos.all()[0].id)
        intento = "3"

        url = "{0}/{1}/{2}/fin_err_t/".format(
            campana_id, contacto_id, intento)

        fastagi_daemon.setup_globals()
        fastagi_daemon.INSERT_FUNCION = do_insert_mock

        agi = FastAGIProtocol()
        agi.variables['agi_network_script'] = url
        agi.finish = mock.MagicMock()

        self.assertEqual(EventoDeContacto.objects.count(), 2)

        # -----

        fastagi_daemon.fastagi_handler(agi)

        self.assertEqual(agi.finish.call_count, 1)
        self.assertEqual(EventoDeContacto.objects.count(), 3)

    def test_fastagi_handler_no_falla_con_url_invalida(self):
        # FIXME: implementar test usando Twisted

        url = "url/no/valida"

        fastagi_daemon.setup_globals()
        fastagi_daemon.INSERT_FUNCION = do_insert_mock

        agi = FastAGIProtocol()
        agi.variables['agi_network_script'] = url
        agi.finish = mock.MagicMock()

        # -----

        fastagi_daemon.fastagi_handler(agi)
        self.assertEqual(agi.finish.call_count, 1)

    def test_fastagi_handler_no_falla_si_insert_lanza_excepcion(self):
        # FIXME: implementar test usando Twisted

        def dangerous_insert(*args, **kwargs):
            raise Exception("ERROR! (deberia ignorarse)")

        url = "url/no/valida"

        fastagi_daemon.setup_globals()
        fastagi_daemon.INSERT_FUNCION = dangerous_insert

        agi = FastAGIProtocol()
        agi.variables['agi_network_script'] = url
        agi.finish = mock.MagicMock()

        # -----

        fastagi_daemon.fastagi_handler(agi)
        self.assertEqual(agi.finish.call_count, 1)


class FastAgiDaemonDoInsertTest(FTSenderBaseTest):

    def test_do_insert_inserta_con_url_valida(self):
        regexes = create_regex()

        campana = self.crear_campana_activa(cant_contactos=2,
            cantidad_canales=1)
        campana_id = str(campana.id)
        contacto_id = str(campana.bd_contacto.contactos.all()[0].id)
        intento = "3"

        url = "{0}/{1}/{2}/fin_err_t/".format(
            campana_id, contacto_id, intento)

        self.assertEqual(EventoDeContacto.objects.count(), 2)

        # -----

        fastagi_daemon.do_insert(
            TwistedReactorMock(),
            tests_fastagi_daemon_views.DjConnectionPoolMock(),
            regexes,
            url
        )

        self.assertEqual(EventoDeContacto.objects.count(), 3)

    def test_do_insert_no_inserta_con_url_invalida(self):
        regexes = create_regex()
        url = "url/no/valida"

        # -----

        with self.assertRaises(UrlNoMatcheaNingunaVista):
            fastagi_daemon.do_insert(
                TwistedReactorMock(),
                tests_fastagi_daemon_views.DjConnectionPoolMock(),
                regexes,
                url
            )
