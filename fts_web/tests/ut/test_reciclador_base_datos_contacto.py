# -*- coding: utf-8 -*-

"""Tests del modulo fts_web.reciclador_base_datos_contacto.reciclador"""

from __future__ import unicode_literals

from fts_web.errors import FtsRecicladoBaseDatosContactoError
from fts_web.models import Campana, BaseDatosContacto
from fts_web.reciclador_base_datos_contacto.reciclador import (
    RecicladorBaseDatosContacto, CampanaEstadoInvalidoError,
    CampanaTipoRecicladoInvalidoError)
from fts_web.tests.utiles import FTSenderBaseTest
import logging as _logging
from mock import Mock, patch

logger = _logging.getLogger(__name__)


class RecicladorBaseDatosContactoTests(FTSenderBaseTest):
    """Unit tests de FinalizadorDeCampanaWorkflow"""

    def test_devuelve_base_datos_original_con_reciclado_total(self):
        campana = Campana(id=1)
        campana.save = Mock()
        campana.bd_contacto = BaseDatosContacto(id=1)
        campana.estado = Campana.ESTADO_DEPURADA

        reciclador = RecicladorBaseDatosContacto()
        reciclador._obtener_campana = Mock(return_value=campana)

        # -----

        bd_reciclada = reciclador.reciclar(campana.pk,
                                           [Campana.TIPO_RECICLADO_TOTAL])

        self.assertEquals(campana.bd_contacto, bd_reciclada)

    def test_falla_con_campana_activa(self):
        campana = Campana(id=1)
        campana.save = Mock()
        campana.bd_contacto = BaseDatosContacto(id=1)
        campana.estado = Campana.ESTADO_ACTIVA

        reciclador = RecicladorBaseDatosContacto()
        reciclador._obtener_campana = Mock(return_value=campana)

        # -----

        with self.assertRaises(CampanaEstadoInvalidoError):
            reciclador.reciclar(campana.pk,
                                [Campana.TIPO_RECICLADO_TOTAL])

    def test_falla_con_reciclado_total_mas_otros(self):
        campana = Campana(id=1)
        campana.save = Mock()
        campana.bd_contacto = BaseDatosContacto(id=1)
        campana.estado = Campana.ESTADO_DEPURADA

        reciclador = RecicladorBaseDatosContacto()
        reciclador._obtener_campana = Mock(return_value=campana)

        # -----

        with self.assertRaises(CampanaTipoRecicladoInvalidoError):
            reciclador.reciclar(campana.pk,
                                [Campana.TIPO_RECICLADO_TOTAL,
                                 Campana.TIPO_RECICLADO_OCUPADOS])

        with self.assertRaises(CampanaTipoRecicladoInvalidoError):
            reciclador.reciclar(campana.pk,
                                [Campana.TIPO_RECICLADO_OCUPADOS,
                                 Campana.TIPO_RECICLADO_TOTAL])

    def test_falla_con_reciclado_pendiente_mas_otros(self):
        campana = Campana(id=1)
        campana.save = Mock()
        campana.bd_contacto = BaseDatosContacto(id=1)
        campana.estado = Campana.ESTADO_DEPURADA

        reciclador = RecicladorBaseDatosContacto()
        reciclador._obtener_campana = Mock(return_value=campana)

        # -----

        with self.assertRaises(CampanaTipoRecicladoInvalidoError):
            reciclador.reciclar(campana.pk,
                                [Campana.TIPO_RECICLADO_OCUPADOS,
                                 Campana.TIPO_RECICLADO_PENDIENTES])

        with self.assertRaises(CampanaTipoRecicladoInvalidoError):
            reciclador.reciclar(campana.pk,
                                [Campana.TIPO_RECICLADO_PENDIENTES,
                                 Campana.TIPO_RECICLADO_OCUPADOS])

    def test_falla_con_tipo_invalido(self):
        campana = Campana(id=1)
        campana.save = Mock()
        campana.bd_contacto = BaseDatosContacto(id=1)
        campana.estado = Campana.ESTADO_DEPURADA

        reciclador = RecicladorBaseDatosContacto()
        reciclador._obtener_campana = Mock(return_value=campana)

        # -----

        with self.assertRaises(CampanaTipoRecicladoInvalidoError):
            reciclador.reciclar(campana.pk,
                                [Campana.TIPO_RECICLADO_OCUPADOS, None])

        with self.assertRaises(CampanaTipoRecicladoInvalidoError):
            reciclador.reciclar(campana.pk,
                                [Campana.TIPO_RECICLADO_OCUPADOS, 12345])

    def test_falla_con_tipo_vacio(self):
        campana = Campana(id=1)
        campana.save = Mock()
        campana.bd_contacto = BaseDatosContacto(id=1)
        campana.estado = Campana.ESTADO_DEPURADA

        reciclador = RecicladorBaseDatosContacto()
        reciclador._obtener_campana = Mock(return_value=campana)

        # -----

        with self.assertRaises(CampanaTipoRecicladoInvalidoError):
            reciclador.reciclar(campana.pk, [])

    @patch('fts_daemon.models.EventoDeContacto.objects_reciclador_contactos.'
           'obtener_contactos_reciclados')
    def test_crea_base_datos_con_reciclado_ocupados(self, func_mock):
        campana = Campana(id=1)
        campana.save = Mock()
        campana.bd_contacto = BaseDatosContacto(id=1)
        campana.estado = Campana.ESTADO_DEPURADA

        bd_contacto = Mock()

        func_mock.return_value = [
            Mock(), Mock(), Mock()]

        reciclador = RecicladorBaseDatosContacto()
        reciclador._obtener_campana = Mock(return_value=campana)
        reciclador._crear_base_datos = Mock(return_value=bd_contacto)

        # -----

        bd_reciclada = reciclador.reciclar(campana.pk,
                                           [Campana.TIPO_RECICLADO_OCUPADOS])
        self.assertEquals(bd_reciclada, bd_contacto)

    @patch('fts_daemon.models.EventoDeContacto.objects_reciclador_contactos.'
           'obtener_contactos_reciclados')
    def test_falla_base_datos_sin_datos_reciclados(self, func_mock):
        campana = Campana(id=1)
        campana.save = Mock()
        campana.bd_contacto = BaseDatosContacto(id=1)
        campana.estado = Campana.ESTADO_DEPURADA

        func_mock.return_value = []

        reciclador = RecicladorBaseDatosContacto()
        reciclador._obtener_campana = Mock(return_value=campana)

        # -----

        with self.assertRaises(FtsRecicladoBaseDatosContactoError):
            reciclador.reciclar(campana.pk,
                                [Campana.TIPO_RECICLADO_OCUPADOS])
