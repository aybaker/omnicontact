# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import datetime
import os

from django.test.utils import override_settings

from fts_web.models import Campana, BaseDatosContacto, Contacto
from fts_web.tests.utiles import FTSenderBaseTest
from fts_daemon.models import EventoDeContacto
from fts_daemon.services.depurador_de_campana import DepuradorDeCampanaWorkflow
import tempfile


def _tmpdir():
    """Crea directorio temporal"""
    return tempfile.mkdtemp(prefix=".fts-tests-", dir="/dev/shm")


def _crea_campana_con_eventos():
    base_dato_contacto = BaseDatosContacto(pk=1)
    base_dato_contacto.save()

    for ic, _ in enumerate(range(10)):
        contacto = Contacto(pk=ic)
        contacto.datos = '["3513368309", "Carlos", "Ilcobich"]'
        contacto.bd_contacto = base_dato_contacto
        contacto.save()

    campana = Campana(pk=1)
    campana.nombre = "Test"
    campana.cantidad_canales = 1
    campana.cantidad_intentos = 1
    campana.segundos_ring = 1
    campana.estado = Campana.ESTADO_FINALIZADA
    campana.bd_contacto = base_dato_contacto
    campana.save()

    for ie, _ in enumerate(range(10)):
        evento_contacto = EventoDeContacto(pk=ie)
        evento_contacto.campana_id = 1
        evento_contacto.contacto_id = ie
        evento_contacto.evento = 1
        evento_contacto.dato = 1
        evento_contacto.save()
    return campana


class ObtenerContactosRecicladosTest(FTSenderBaseTest):

    @override_settings(MEDIA_ROOT=_tmpdir())
    def test_obtener_contactos_pendientes(self):
        campana = _crea_campana_con_eventos()

        DepuradorDeCampanaWorkflow().depurar(campana.id)
        campana = Campana.objects.get(id=campana.id)

        contactos_pendientes = EventoDeContacto.objects_reciclador_contactos.\
            _obtener_contactos_pendientes(campana)
        self.assertEqual(len(contactos_pendientes), 10)

        # Verifico la estructura del objeto devuelto.
        for contacto_pendiente in contactos_pendientes:
            self.assertTrue(type(contacto_pendiente[0] == int))

    @override_settings(MEDIA_ROOT=_tmpdir())
    def test_obtener_contactos_ocupados(self):
        campana = _crea_campana_con_eventos()

        DepuradorDeCampanaWorkflow().depurar(campana.id)
        campana = Campana.objects.get(id=campana.id)

        contactos_ocupados = EventoDeContacto.objects_reciclador_contactos.\
            _obtener_contactos_ocupados(campana)
        self.assertEqual(len(contactos_ocupados), 0)

        # Verifico la estructura del objeto devuelto.
        for contacto_ocupado in contactos_ocupados:
            self.assertTrue(type(contacto_ocupado[0] == int))

    @override_settings(MEDIA_ROOT=_tmpdir())
    def test_obtener_contactos_no_contestados(self):
        campana = _crea_campana_con_eventos()

        DepuradorDeCampanaWorkflow().depurar(campana.id)
        campana = Campana.objects.get(id=campana.id)

        contactos_no_contestados = EventoDeContacto.\
            objects_reciclador_contactos._obtener_contactos_no_contestados(
                campana)
        self.assertEqual(len(contactos_no_contestados), 0)

        # Verifico la estructura del objeto devuelto.
        for contacto_no_contestado in contactos_no_contestados:
            self.assertTrue(type(contacto_no_contestado[0] == int))

    @override_settings(MEDIA_ROOT=_tmpdir())
    def test_obtener_contactos_numero_erroneo(self):
        campana = _crea_campana_con_eventos()

        DepuradorDeCampanaWorkflow().depurar(campana.id)
        campana = Campana.objects.get(id=campana.id)

        contactos_numeros_erroneos = EventoDeContacto.\
            objects_reciclador_contactos._obtener_contactos_numero_erroneo(
                campana)
        self.assertEqual(len(contactos_numeros_erroneos), 0)

        # Verifico la estructura del objeto devuelto.
        for contactos_numero_erroneo in contactos_numeros_erroneos:
            self.assertTrue(type(contactos_numero_erroneo[0] == int))

    @override_settings(MEDIA_ROOT=_tmpdir())
    def test_obtener_contactos_llamada_erronea(self):
        campana = _crea_campana_con_eventos()

        DepuradorDeCampanaWorkflow().depurar(campana.id)
        campana = Campana.objects.get(id=campana.id)

        contactos_llamadas_erroneas = EventoDeContacto.\
            objects_reciclador_contactos._obtener_contactos_llamada_erronea(
                campana)
        self.assertEqual(len(contactos_llamadas_erroneas), 0)

        # Verifico la estructura del objeto devuelto.
        for contactos_llamada_erronea in contactos_llamadas_erroneas:
            self.assertTrue(type(contactos_llamada_erronea[0] == int))
