# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import datetime
import os

from django.test.utils import override_settings

from fts_web.models import Campana
from fts_web.tests.utiles import FTSenderBaseTest
from fts_daemon.models import EventoDeContacto
from fts_daemon.services.depurador_de_campana import DepuradorDeCampanaWorkflow
import tempfile


def _tmpdir():
    """Crea directorio temporal"""
    return tempfile.mkdtemp(prefix=".fts-tests-", dir="/dev/shm")


class ObtenerContactosRecicladosTest(FTSenderBaseTest):

    @override_settings(MEDIA_ROOT=_tmpdir())
    def test_obtener_contactos_pendientes(self):
        # Verifico que devuelva la cantidad de pendientes correctos.
        campana = self._crea_campana_emula_procesamiento(
            evento=EventoDeContacto.EVENTO_DAEMON_ORIGINATE_SUCCESSFUL,
            cantidad_eventos=20)
        DepuradorDeCampanaWorkflow().depurar(campana.id)
        campana = Campana.objects.get(id=campana.id)
        contactos_pendientes = EventoDeContacto.objects_reciclador_contactos.\
            _obtener_contactos_pendientes(campana)
        self.assertEqual(len(contactos_pendientes), 80)

        # Verifico la estructura del objeto devuelto.
        for contacto_pendiente in contactos_pendientes:
            self.assertTrue(type(contacto_pendiente[0] == int))

    @override_settings(MEDIA_ROOT=_tmpdir())
    def test_obtener_contactos_ocupados(self):
        # Verifico que devuelva la cantidad de ocupados correctos.
        campana = self._crea_campana_emula_procesamiento(
            evento=EventoDeContacto.EVENTO_ASTERISK_DIALSTATUS_BUSY,
            cantidad_eventos=20)
        DepuradorDeCampanaWorkflow().depurar(campana.id)
        campana = Campana.objects.get(id=campana.id)
        contactos_ocupados = EventoDeContacto.objects_reciclador_contactos.\
            _obtener_contactos_ocupados(campana)
        self.assertEqual(len(contactos_ocupados), 20)

        # Verifico la estructura del objeto devuelto.
        for contacto_ocupado in contactos_ocupados:
            self.assertTrue(type(contacto_ocupado[0] == int))

    @override_settings(MEDIA_ROOT=_tmpdir())
    def test_obtener_contactos_no_contestados(self):
        # Verifico que devuelva la cantidad de no contestados correctos.
        campana = self._crea_campana_emula_procesamiento(
            evento=EventoDeContacto.EVENTO_ASTERISK_DIALSTATUS_NOANSWER,
            cantidad_eventos=20)
        DepuradorDeCampanaWorkflow().depurar(campana.id)
        campana = Campana.objects.get(id=campana.id)
        contactos_no_contestados = EventoDeContacto.\
            objects_reciclador_contactos._obtener_contactos_no_contestados(
                campana)
        self.assertEqual(len(contactos_no_contestados), 20)

        # Verifico la estructura del objeto devuelto.
        for contacto_no_contestado in contactos_no_contestados:
            self.assertTrue(type(contacto_no_contestado[0] == int))

    @override_settings(MEDIA_ROOT=_tmpdir())
    def test_obtener_contactos_numero_erroneo(self):
        # Verifico que devuelva la cantidad de contactos erróneos correctos.
        campana = self._crea_campana_emula_procesamiento(
            evento=EventoDeContacto.EVENTO_ASTERISK_DIALSTATUS_CONGESTION,
            cantidad_eventos=20)
        DepuradorDeCampanaWorkflow().depurar(campana.id)
        campana = Campana.objects.get(id=campana.id)
        contactos_numeros_erroneos = EventoDeContacto.\
            objects_reciclador_contactos._obtener_contactos_numero_erroneo(
                campana)
        self.assertEqual(len(contactos_numeros_erroneos), 20)

        # Verifico la estructura del objeto devuelto.
        for contactos_numero_erroneo in contactos_numeros_erroneos:
            self.assertTrue(type(contactos_numero_erroneo[0] == int))

    @override_settings(MEDIA_ROOT=_tmpdir())
    def test_obtener_contactos_llamada_erronea(self):
        # Verifico que devuelva la cantidad de llamadas erróneas correctas.
        campana = self._crea_campana_emula_procesamiento(
            evento=EventoDeContacto.EVENTO_ASTERISK_DIALSTATUS_CHANUNAVAIL,
            cantidad_eventos=20)
        DepuradorDeCampanaWorkflow().depurar(campana.id)
        campana = Campana.objects.get(id=campana.id)
        contactos_llamadas_erroneas = EventoDeContacto.\
            objects_reciclador_contactos._obtener_contactos_llamada_erronea(
                campana)
        self.assertEqual(len(contactos_llamadas_erroneas), 20)

        # Verifico la estructura del objeto devuelto.
        for contactos_llamada_erronea in contactos_llamadas_erroneas:
            self.assertTrue(type(contactos_llamada_erronea[0] == int))
