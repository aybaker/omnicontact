# -*- coding: utf-8 -*-

"""Tests generales"""

from __future__ import unicode_literals

from django.test.utils import override_settings
from fts_daemon.llamador_contacto import procesar_contacto
from fts_daemon.models import EventoDeContacto
from fts_tests.tests.tests_asterisk_ami_http_mocks import \
    AsteriskAmiHttpClientBaseMock, AAHCOriginateErrorMock, AAHCAuthFailMock
from fts_tests.tests.utiles import EventoDeContactoAssertUtilesMixin
from fts_web.tests.utiles import FTSenderBaseTest
import logging as _logging
from fts_daemon.poll_daemon.campana_tracker import DatosParaRealizarLlamada


logger = _logging.getLogger(__name__)

CONT_PROG = EventoDeContacto.EVENTO_CONTACTO_PROGRAMADO
D_INI_INT = EventoDeContacto.EVENTO_DAEMON_INICIA_INTENTO
D_ORIG_SUC = EventoDeContacto.EVENTO_DAEMON_ORIGINATE_SUCCESSFUL
D_ORIG_FAIL = EventoDeContacto.EVENTO_DAEMON_ORIGINATE_FAILED
D_ORIG_INT_ERR = EventoDeContacto.EVENTO_DAEMON_ORIGINATE_INTERNAL_ERROR


class ProcesarContactoRegistraEventosTest(FTSenderBaseTest,
    EventoDeContactoAssertUtilesMixin):
    """Testea que el daemon registre los eventos que debe registrar"""

    def _get_logger(self):
        return logger

    def test_registra_intento_y_originate_ok(self):
        """Testea procesar_contacto() y EventoDeContacto"""

        CANT = 5
        mock = AsteriskAmiHttpClientBaseMock.NAME

        # CREAMOS la campaña
        campana = self.crear_campana_activa(cant_contactos=CANT)
        self._assertCountEventos(campana, CONT_PROG, checks={CONT_PROG: 5})
        pendientes = self._assertPendientes(campana, CANT, 0)

        contacto1_id = pendientes[0].id_contacto
        contacto2_id = pendientes[1].id_contacto

        #
        # PROCESAMOS 1er contacto (1er intento)
        #
        with override_settings(FTS_ASTERISK_HTTP_CLIENT=mock):
            ok = procesar_contacto(DatosParaRealizarLlamada(
                campana, contacto1_id, '111', 0,
                self.crear_dict_datos_extras()))

        self.assertTrue(ok)

        # Chequeamos
        self._assertCountEventos(campana, CONT_PROG, D_INI_INT, D_ORIG_SUC,
            checks={CONT_PROG: CANT, D_INI_INT: 1, D_ORIG_SUC: 1})
        self._assertPendientes(campana, CANT, 0, 1)

        #
        # PROCESAMOS 2do contacto (1er intento)
        #
        with override_settings(FTS_ASTERISK_HTTP_CLIENT=mock):
            ok = procesar_contacto(DatosParaRealizarLlamada(
                campana, contacto2_id, '222', 0,
                self.crear_dict_datos_extras()))

        self.assertTrue(ok)

        # Chequeamos
        self._assertCountEventos(campana, CONT_PROG, D_INI_INT, D_ORIG_SUC,
            checks={CONT_PROG: CANT, D_INI_INT: 2, D_ORIG_SUC: 2})
        self._assertPendientes(campana, CANT, 0, 1)

    def test_registra_intento_y_originate_error(self):
        """Testea procesar_contacto() y EventoDeContacto"""

        CANT = 5
        mock = AAHCOriginateErrorMock.NAME

        # CREAMOS la campaña
        campana = self.crear_campana_activa(cant_contactos=CANT)
        self._assertCountEventos(campana, CONT_PROG, checks={CONT_PROG: 5})
        pendientes = self._assertPendientes(campana, CANT, 0)

        contacto1_id = pendientes[0].id_contacto
        contacto2_id = pendientes[1].id_contacto

        #
        # PROCESAMOS 1er contacto (1er intento) => FALLA
        #
        with override_settings(FTS_ASTERISK_HTTP_CLIENT=mock):
            ok = procesar_contacto(DatosParaRealizarLlamada(
                campana, contacto1_id, '111', 0,
                self.crear_dict_datos_extras()))

        self.assertFalse(ok)

        # Chequeamos
        self._assertCountEventos(campana, CONT_PROG, D_INI_INT, D_ORIG_FAIL,
            checks={CONT_PROG: CANT, D_INI_INT: 1, D_ORIG_FAIL: 1})
        self._assertPendientes(campana, CANT, 0, 1)

        #
        # PROCESAMOS 2do contacto (1er intento), con OTRO mock
        #
        mock = AsteriskAmiHttpClientBaseMock.NAME
        with override_settings(FTS_ASTERISK_HTTP_CLIENT=mock):
            ok = procesar_contacto(DatosParaRealizarLlamada(
                campana, contacto2_id, '222', 0,
                self.crear_dict_datos_extras()))

        self.assertTrue(ok)

        # Chequeamos
        self._assertCountEventos(campana, CONT_PROG, D_INI_INT, D_ORIG_SUC,
            D_ORIG_FAIL, checks={CONT_PROG: CANT, D_INI_INT: 2,
                D_ORIG_FAIL: 1, D_ORIG_SUC: 1})
        self._assertPendientes(campana, CANT, 0, 1)

    def test_registra_intento_y_error_interno(self):
        """Testea procesar_contacto() y EventoDeContacto"""

        CANT = 5
        mock = AAHCAuthFailMock.NAME

        # CREAMOS la campaña
        campana = self.crear_campana_activa(cant_contactos=CANT)
        self._assertCountEventos(campana, CONT_PROG, checks={CONT_PROG: 5})
        pendientes = self._assertPendientes(campana, CANT, 0)

        contacto1_id = pendientes[0].id_contacto

        #
        # PROCESAMOS 1er contacto (1er intento) => FALLA
        #
        with override_settings(FTS_ASTERISK_HTTP_CLIENT=mock):
            ok = procesar_contacto(DatosParaRealizarLlamada(
                campana, contacto1_id, '111', 0,
                self.crear_dict_datos_extras()))

        self.assertFalse(ok)

        # Chequeamos
        self._assertCountEventos(campana, CONT_PROG, D_INI_INT, D_ORIG_INT_ERR,
            checks={CONT_PROG: CANT, D_INI_INT: 1, D_ORIG_INT_ERR: 1})
        self._assertPendientes(campana, CANT, 0, 1)

    def test_request_http_falla(self):
        """Testea procesar_contacto() y EventoDeContacto"""

        CANT = 5

        # CREAMOS la campaña
        campana = self.crear_campana_activa(cant_contactos=CANT)
        self._assertCountEventos(campana, CONT_PROG, checks={CONT_PROG: 5})
        pendientes = self._assertPendientes(campana, CANT, 0)

        contacto1_id = pendientes[0].id_contacto

        #
        # PROCESAMOS 1er contacto (1er intento) => FALLA
        #
        with override_settings(HTTP_AMI_URL="http://127.0.0.1:4"):
            ok = procesar_contacto(DatosParaRealizarLlamada(
                campana, contacto1_id, '111', 0,
                self.crear_dict_datos_extras()))

        self.assertFalse(ok)

        self.dump_count_eventos(campana)

        # Chequeamos
        self._assertPendientes(campana, CANT, 0, 1)
        self._assertCountEventos(campana, CONT_PROG, D_INI_INT, D_ORIG_INT_ERR,
            checks={CONT_PROG: CANT, D_INI_INT: 1, D_ORIG_INT_ERR: 1})
