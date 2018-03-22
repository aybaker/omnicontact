# -*- coding: utf-8 -*-

"""Tests generales"""

from __future__ import unicode_literals

from unittest.case import skipIf
from django.conf import settings
from fts_daemon.models import EventoDeContacto
from fts_daemon.poll_daemon.campana_tracker import CampanaTracker, \
    NoMasContactosEnCampana, CampanaNoEnEjecucion, \
    TodosLosContactosPendientesEstanEnCursoError, DatosParaRealizarLlamada
from fts_web.models import Campana
from fts_web.tests.utiles import FTSenderBaseTest
import logging as _logging
import pprint
from mock import Mock
import random


logger = _logging.getLogger(__name__)

CONT_PROG = EventoDeContacto.EVENTO_CONTACTO_PROGRAMADO
D_INI_INT = EventoDeContacto.EVENTO_DAEMON_INICIA_INTENTO
D_ORIG_SUC = EventoDeContacto.EVENTO_DAEMON_ORIGINATE_SUCCESSFUL

EVENTO_FINALIZADOR = EventoDeContacto.objects.\
            get_eventos_finalizadores()[0]


class PollDaemonTestUtilsMixin():

    def _finaliza(self, contacto_id, intento, campana=None):
        """Genera evento `EVENTO_FINALIZADOR` para campana"""
        campana = campana or getattr(self, 'campana')
        EventoDeContacto.objects.create(
            campana_id=campana.id,
            contacto_id=contacto_id,
            evento=EVENTO_FINALIZADOR,
            dato=intento)

    def _assertContacto(self, contacto_id, telefono, campana, metadata):
        """Assert q' contacto pertenece a campana"""
        contacto = campana.bd_contacto.contactos.filter(id=contacto_id).get()
        self.assertTrue(contacto)

        telefono_from_contacto = metadata.obtener_telefono_de_dato_de_contacto(
            contacto.datos)
        self.assertEquals(telefono, telefono_from_contacto)

    def _code(self, code):
        """
        client = AsteriskHttpClient()
        with override_settings(HTTP_AMI_URL=self._code('login-ok')):
            client.login()
        """
        asterisk = settings.ASTERISK
        asterisk['HTTP_AMI_URL'] = self.live_server_url + \
            "/asterisk-ami-http/" + code
        return asterisk

    def _crear_1_campana(self, tamano=10, cantidad_canales=2):
        assert tamano > cantidad_canales
        campana = self.crear_campana_activa(cant_contactos=tamano,
            cantidad_canales=cantidad_canales)
        self.crea_todas_las_actuaciones(campana)
        return campana

    def _crear_3_campanas(self, tamano=10, cantidad_canales=2):
        """
        Crea 3 campanas ACTIVAS con 10 contactos cada una (default),
        con un limite de 2 canales para cada campana.
        """
        return [self._crear_1_campana(tamano=tamano,
            cantidad_canales=cantidad_canales) for _ in (1, 2, 3,)]


#==============================================================================
# CampanaTracker
#==============================================================================

class CampanaTrackerTests(FTSenderBaseTest, PollDaemonTestUtilsMixin):

    def setUp(self):
        self.campana, self.campana1, self.campana3 = \
            self._crear_3_campanas()

        self.tracker = CampanaTracker(self.campana)
        self.tracker._calculador_de_fetch._fetch_min = 3
        self.tracker._calculador_de_fetch._fetch_max = 5

        self.assertEquals(self.tracker.cache, [])

    def test_populate_cache_populates_the_cache(self):
        # Ejecutamos _populate_cache()
        self.tracker._populate_cache()

        self.assertGreaterEqual(len(self.tracker.cache),
            self.tracker._calculador_de_fetch._fetch_min)
        self.assertLessEqual(len(self.tracker.cache),
            self.tracker._calculador_de_fetch._fetch_max)

    def test_next_llama_a_populate_cache(self):
        self.tracker.next()

        self.assertGreaterEqual(len(self.tracker.cache) + 1,
            self.tracker._calculador_de_fetch._fetch_min)
        self.assertLessEqual(len(self.tracker.cache) + 1,
            self.tracker._calculador_de_fetch._fetch_max)

    def test_next_lanza_NoMasContactosEnCampana(self):
        for _ in range(0, 10):
            # si no reseteamos llamadas en curso, nos dara problemas
            datos_para_realizar_llamada = self.tracker.next()
            assert isinstance(datos_para_realizar_llamada,
                              DatosParaRealizarLlamada)
            campana = datos_para_realizar_llamada.campana
            contacto_id = datos_para_realizar_llamada.id_contacto
            telefono = datos_para_realizar_llamada.telefono
            intentos = datos_para_realizar_llamada.intentos

            metadata = campana.bd_contacto.get_metadata()

            self.tracker.contactos_en_curso = []
            self.assertEquals(self.campana, campana)
            self._assertContacto(contacto_id, telefono, campana, metadata)
            self.assertEquals(intentos, 0)
            self._finaliza(contacto_id, 0)

        with self.assertRaises(NoMasContactosEnCampana):
            self.tracker.next()

    def test_next_lanza_CampanaNoEnEjecucion(self):
        self.tracker.next()
        self.campana.pausar()

        with self.assertRaises(CampanaNoEnEjecucion):
            self.tracker.next()


class CampanaTrackerActivacionTests(FTSenderBaseTest,
    PollDaemonTestUtilsMixin):

    def setUp(self):
        self.campana = self._crear_1_campana(2, 1)
        self.tracker = CampanaTracker(self.campana)
        self.assertTrue(self.tracker.activa)

    def assertDesactiva(self):
        self.assertFalse(self.tracker.activa)
        self.assertEquals(self.tracker._activa, False)
        self.assertEquals(self.tracker.campana, self.campana)
        self.assertEquals(self.tracker.cache, None)
        self.assertEquals(self.tracker.actuacion, None)

    def assertActiva(self):
        self.assertTrue(self.tracker.activa)
        self.assertTrue(self.tracker._activa)
        self.assertEquals(self.tracker.campana, self.campana)
        self.assertEquals(self.tracker.cache, [])
        self.assertTrue(self.tracker.actuacion is not None)

    # Tests

    def test_desactivar_reactivar(self):
        self.tracker.desactivar()
        self.assertDesactiva()

    def test_reactivar(self):
        self.tracker.desactivar()
        self.tracker.reactivar(self.campana)
        self.assertActiva()

    def test_reactivar_si_corresponde(self):
        self.tracker.desactivar()
        self.tracker.reactivar_si_corresponde(self.campana)
        self.assertActiva()

        fake_c1 = Campana(id=self.campana.id)
        self.tracker.reactivar_si_corresponde(fake_c1)
        self.assertActiva()

    def test_reactivar_con_campana_invalida_falla(self):
        c2 = Campana(id=self.campana.id + 10000)
        self.tracker.desactivar()
        with self.assertRaises(AssertionError):
            self.tracker.reactivar(c2)

    def test_update_con_campana_invalida_falla(self):
        c2 = Campana(id=self.campana.id + 10000)
        with self.assertRaises(AssertionError):
            self.tracker.update_campana(c2)


class TestTodosLosContactosPendientesEstanEnCursoError(FTSenderBaseTest,
    PollDaemonTestUtilsMixin):
    """Testea generacion de TodosLosContactosPendientesEstanEnCursoError"""

    def test_lanza_cuando_demas_ccto_estan_finalizados(self):
        """Test que se lanza 'TodosLosContactosPendientesEstanEnCursoError'
        cuando los contactos pendientes ya estan en ejecucion,
        y los demas contactos de la campana estan finalizados.
        """

        campana = self.crear_campana_activa(cant_contactos=10,
            cantidad_canales=3, cantidad_intentos=2)
        self.crea_todas_las_actuaciones(campana)
        tracker = CampanaTracker(campana)
        tracker._calculador_de_fetch._fetch_min = 3
        tracker._calculador_de_fetch._fetch_max = 5
        self.assertEquals(tracker.cache, [])

        for _ in range(0, 9):
            datos_para_realizar_llamada = tracker.next()
            assert isinstance(datos_para_realizar_llamada,
                              DatosParaRealizarLlamada)
            contacto_id = datos_para_realizar_llamada.id_contacto
            intentos = datos_para_realizar_llamada.intentos

            self.assertEquals(intentos, 0)
            self._finaliza(contacto_id, 1, campana=campana)
            tracker.contactos_en_curso = []

        tracker.next()  # Ponemos en curso el ultimo pendiente

        """Estado actual:

        F -> finalizados
        c -> en curso
        +-------------------+
        |F|F|F|F|F|F|F|F|F|c| 1er intento
        +-------------------+
        |x|x|x|x|x|x|x|x|x| | 2do intento
        +-------------------+
        """

        with self.assertRaises(TodosLosContactosPendientesEstanEnCursoError):
            tracker.next()

    def test_no_lanza_cuando_hay_ccto_con_intentos_pendientes(self):
        """Test que se lanza 'TodosLosContactosPendientesEstanEnCursoError'
        cuando todos los contactos pendientes estan en ejecucion,
        y los demas contactos de la campana estan finalizados.
        """

        campana = self.crear_campana_activa(cant_contactos=10,
            cantidad_canales=3, cantidad_intentos=2)
        self.crea_todas_las_actuaciones(campana)
        tracker = CampanaTracker(campana)
        tracker._calculador_de_fetch._fetch_min = 3
        tracker._calculador_de_fetch._fetch_max = 5

        self.assertEquals(tracker.cache, [])

        for _ in range(0, 9):
            datos_para_realizar_llamada = tracker.next()
            assert isinstance(datos_para_realizar_llamada,
                              DatosParaRealizarLlamada)
            contacto_id = datos_para_realizar_llamada.id_contacto
            intentos = datos_para_realizar_llamada.intentos
            self.assertEquals(intentos, 0)
            self.registra_evento_de_intento(campana.id,
                contacto_id, 1)
            tracker.contactos_en_curso = []

        # Ponemos en curso el ultimo pendiente del 1er intento
        datos_para_realizar_llamada = tracker.next()
        assert isinstance(datos_para_realizar_llamada,
                          DatosParaRealizarLlamada)
        contacto_id = datos_para_realizar_llamada.id_contacto
        intentos = datos_para_realizar_llamada.intentos
        self.assertEquals(intentos, 0)

        """ Estado actual
        i -> intentado
        c -> en curso
        +-------------------+
        |i|i|i|i|i|i|i|i|i|c| 1er intento
        +-------------------+
        | | | | | | | | | | | 2do intento
        +-------------------+
        """

        datos_para_realizar_llamada = tracker.next()
        assert isinstance(datos_para_realizar_llamada,
                          DatosParaRealizarLlamada)
        contacto_id = datos_para_realizar_llamada.id_contacto
        intentos = datos_para_realizar_llamada.intentos
        self.assertEquals(intentos, 1)

        """ Estado actual
        i -> intentado
        c -> en curso
        +-------------------+
        |i|i|i|i|i|i|i|i|i|c| 1er intento
        +-------------------+
        |c| | | | | | | | | | 2do intento
        +-------------------+
        """

    def test_lanza_cuando_ccto_con_intentos_pendientes_estan_en_curso(self):
        """Test que se lanza 'TodosLosContactosPendientesEstanEnCursoError'
        cuando los contactos pendientes ya estan en ejecucion,
        y los demas contactos de la campana estan finalizados.
        """

        campana = self.crear_campana_activa(cant_contactos=10,
            cantidad_canales=3, cantidad_intentos=2)
        self.crea_todas_las_actuaciones(campana)
        tracker = CampanaTracker(campana)
        tracker._calculador_de_fetch._fetch_min = 3
        tracker._calculador_de_fetch._fetch_max = 5
        self.assertEquals(tracker.cache, [])

        for _ in range(0, 9):
            datos_para_realizar_llamada = tracker.next()
            assert isinstance(datos_para_realizar_llamada,
                              DatosParaRealizarLlamada)
            contacto_id = datos_para_realizar_llamada.id_contacto
            intentos = datos_para_realizar_llamada.intentos

            self.assertEquals(intentos, 0)
            self.registra_evento_de_intento(campana.id, contacto_id, 1)
            tracker.contactos_en_curso = []

        # Ponemos en curso el ultimo pendiente del 1er intento
        datos_para_realizar_llamada = tracker.next()
        assert isinstance(datos_para_realizar_llamada,
                          DatosParaRealizarLlamada)
        contacto_id = datos_para_realizar_llamada.id_contacto
        intentos = datos_para_realizar_llamada.intentos

        self.assertEquals(intentos, 0)
        self.registra_evento_de_intento(campana.id, contacto_id, 1)

        contactos_en_curso_ultimi_de_1er_intento = list(
            tracker.contactos_en_curso)

        """Estado actual:

        F -> finalizados
        c -> en curso
        +-------------------+
        |i|i|i|i|i|i|i|i|i|c| 1er intento
        +-------------------+
        | | | | | | | | | | | 2do intento
        +-------------------+
        """

        # Arrancamos 2do intento
        for _ in range(0, 9):
            datos_para_realizar_llamada = tracker.next()
            assert isinstance(datos_para_realizar_llamada,
                              DatosParaRealizarLlamada)
            contacto_id = datos_para_realizar_llamada.id_contacto
            intentos = datos_para_realizar_llamada.intentos

            self.assertEquals(intentos, 1)
            self.registra_evento_de_intento(campana.id, contacto_id, 2)
            tracker.contactos_en_curso = list(
                contactos_en_curso_ultimi_de_1er_intento)

        """Estado actual:

        F -> finalizados
        c -> en curso
        +-------------------+
        |i|i|i|i|i|i|i|i|i|c| 1er intento
        +-------------------+
        |i|i|i|i|i|i|i|i|i| | 2do intento
        +-------------------+
        """

        with self.assertRaises(TodosLosContactosPendientesEstanEnCursoError):
            tracker.next()

        tracker.contactos_en_curso = []

        datos_para_realizar_llamada = tracker.next()
        assert isinstance(datos_para_realizar_llamada,
                          DatosParaRealizarLlamada)
        contacto_id = datos_para_realizar_llamada.id_contacto
        intentos = datos_para_realizar_llamada.intentos

        self.assertEquals(intentos, 1)


class CampanaTrackerNextChequeaEstadoCampana(FTSenderBaseTest):
    """Chequea que next() genere CampanaNoEnEjecucion si la
    campana cambia de estado
    """

    def test_lanza_CampanaNoEnEjecucion_con_cache_vacio(self):

        # 2 contactos / 1 cacheados
        campana = self.crear_campana_activa(cant_contactos=10,
            cantidad_canales=3)
        self.crea_todas_las_actuaciones(campana)

        tracker = CampanaTracker(campana)
        tracker._calculador_de_fetch.get_fetch_size = Mock(return_value=1)
        self.assertEquals(tracker.cache, [])  # CACHE VACIO

        tracker.next()

        Campana.objects.get(pk=campana.id).pausar()

        with self.assertRaises(CampanaNoEnEjecucion):
            tracker.next()

    def test_lanza_CampanaNoEnEjecucion_con_datos_cacheados(self):

        # 2 contactos / 1 cacheados
        campana = self.crear_campana_activa(cant_contactos=10,
            cantidad_canales=3)
        self.crea_todas_las_actuaciones(campana)

        tracker = CampanaTracker(campana)
        tracker._calculador_de_fetch.get_fetch_size = Mock(return_value=2)
        self.assertEquals(len(tracker.cache), 0)

        tracker.next()

        self.assertEquals(len(tracker.cache), 1)  # CACHE CON DATOS

        Campana.objects.get(pk=campana.id).pausar()

        with self.assertRaises(CampanaNoEnEjecucion):
            tracker.next()


class TestsDevuelvePendientesCorrectamenteYDetectaLimiteDeIntentos(
    FTSenderBaseTest, PollDaemonTestUtilsMixin):
    """Chequea que next() no devuelva contactos cuando se haya
    alcanzado el limite de intentos, con distintos valores de cache.
    """

    def _test_genera_NMCEC_al_superar_cant_intentos(self,
        fetch_min, fetch_max, reseteador_contactos_en_curso):
        campana = self.crear_campana_activa(cant_contactos=10,
            cantidad_canales=2, cantidad_intentos=2)
        self.crea_todas_las_actuaciones(campana)
        tracker = CampanaTracker(campana)

        tracker._calculador_de_fetch._fetch_min = fetch_min
        tracker._calculador_de_fetch._fetch_max = fetch_max

        self.assertEquals(tracker.cache, [])

        for iter_nro in range(0, 10):
            datos_para_realizar_llamada = tracker.next()
            assert isinstance(datos_para_realizar_llamada,
                              DatosParaRealizarLlamada)
            contacto_id = datos_para_realizar_llamada.id_contacto
            intentos = datos_para_realizar_llamada.intentos

            self.assertEquals(intentos, 0, "next() a devuelto "
                "contacto de intento != 0 (intentos == {0}) en "
                "interacion {1} - fetch_min: {2}, fetch_max: {3}".format(
                    intentos, iter_nro, fetch_min, fetch_max))
            self.registra_evento_de_intento(campana.id,
                contacto_id, 1)
            reseteador_contactos_en_curso(tracker)

        for iter_nro in range(0, 10):
            datos_para_realizar_llamada = tracker.next()
            assert isinstance(datos_para_realizar_llamada,
                              DatosParaRealizarLlamada)
            contacto_id = datos_para_realizar_llamada.id_contacto
            intentos = datos_para_realizar_llamada.intentos

            self.assertEquals(intentos, 1, "next() a devuelto "
                "contacto de intento != 1 (intentos == {0}) en "
                "interacion {1} - fetch_min: {2}, fetch_max: {3}".format(
                    intentos, iter_nro, fetch_min, fetch_max))
            self.registra_evento_de_intento(campana.id,
                contacto_id, 2)
            reseteador_contactos_en_curso(tracker)

        with self.assertRaises(NoMasContactosEnCampana):
            tracker.next()

    def test_genera_NMCEC_al_superar_cant_intentos_1(self):

        def reseteador_contactos_en_curso_1(tracker):
            tracker.contactos_en_curso = []

        def reseteador_contactos_en_curso_2(tracker):
            if len(tracker.contactos_en_curso) > 1:
                tracker.contactos_en_curso = \
                    tracker.contactos_en_curso[1:]

        values = (1, 2, 3, 4, 5, 6, 9, 10, 11, 15)
        for fetch_min in values:
            for fetch_max in values:
                if fetch_min > fetch_max:
                    continue
                self._test_genera_NMCEC_al_superar_cant_intentos(
                    fetch_min, fetch_max, reseteador_contactos_en_curso_1)
                self._test_genera_NMCEC_al_superar_cant_intentos(
                    fetch_min, fetch_max, reseteador_contactos_en_curso_2)


class TestsDetectaTodosLosContactosFinalizados(FTSenderBaseTest,
    PollDaemonTestUtilsMixin):
    """Chequea que next() no devuelva contactos cuando se hayan
    procesado todos los contactos.
    """

    def test_genera_NoMasContactosEnCampana_con_datos_cacheados(self):

        campana = self.crear_campana_activa(cant_contactos=2,
            cantidad_canales=1, cantidad_intentos=2)
        self.crea_todas_las_actuaciones(campana)

        tracker = CampanaTracker(campana)
        tracker._calculador_de_fetch.get_fetch_size = Mock(return_value=2)
        self.assertEquals(len(tracker.cache), 0)

        # Populate cache
        datos_para_realizar_llamada = tracker.next()
        assert isinstance(datos_para_realizar_llamada,
                          DatosParaRealizarLlamada)
        campana = datos_para_realizar_llamada.campana
        contacto_id = datos_para_realizar_llamada.id_contacto

        self.assertEquals(len(tracker.cache), 1)
        self._finaliza(contacto_id, 1, campana=campana)

        # Reseteamos en curso
        tracker.contactos_en_curso = []

        # Ejecuta next()
        datos_para_realizar_llamada = tracker.next()
        assert isinstance(datos_para_realizar_llamada,
                          DatosParaRealizarLlamada)
        campana = datos_para_realizar_llamada.campana
        contacto_id = datos_para_realizar_llamada.id_contacto

        self._finaliza(contacto_id, 1, campana=campana)
        self.assertEquals(len(tracker.cache), 0)

        # Reseteamos en curso
        tracker.contactos_en_curso = []

        with self.assertRaises(NoMasContactosEnCampana):
            tracker.next()

    def test_genera_NoMasContactosEnCampana_sin_datos_cacheados(self):

        campana = self.crear_campana_activa(cant_contactos=2,
            cantidad_canales=1, cantidad_intentos=2)
        self.crea_todas_las_actuaciones(campana)

        tracker = CampanaTracker(campana)
        tracker._calculador_de_fetch.get_fetch_size = Mock(return_value=1)
        self.assertEquals(len(tracker.cache), 0)

        # Populate cache
        datos_para_realizar_llamada = tracker.next()
        assert isinstance(datos_para_realizar_llamada,
                          DatosParaRealizarLlamada)
        campana = datos_para_realizar_llamada.campana
        contacto_id = datos_para_realizar_llamada.id_contacto

        self.assertEquals(len(tracker.cache), 0)
        self._finaliza(contacto_id, 1, campana=campana)

        # Reseteamos en curso
        tracker.contactos_en_curso = []

        datos_para_realizar_llamada = tracker.next()
        assert isinstance(datos_para_realizar_llamada,
                          DatosParaRealizarLlamada)
        campana = datos_para_realizar_llamada.campana
        contacto_id = datos_para_realizar_llamada.id_contacto

        self.assertEquals(len(tracker.cache), 0)
        self._finaliza(contacto_id, 1, campana=campana)

        # Reseteamos en curso
        tracker.contactos_en_curso = []

        with self.assertRaises(NoMasContactosEnCampana):
            tracker.next()

    # Esto no se pude probar todavia, porque el next()
    # puede llegar a devolver siempre el mismo contacto,
    # ya que todavia no controlamos contactos devueltos
    # recientemente
    @skipIf(True, "Todavia no se puede implementar este test")
    def test_2_contactos_1_cache(self):
        pass
        #EVENTO_FINALIZADOR = EventoDeContacto.objects.\
        #    get_eventos_finalizadores()[0]
        #
        #campana = self.crear_campana_activa(cant_contactos=2,
        #    cantidad_canales=99, cantidad_intentos=1)
        #self.crea_todas_las_actuaciones(campana)
        #
        #tracker = CampanaTracker(campana)
        #tracker.fetch_min = 2
        #tracker.fetch_max = 2
        #self.assertEquals(tracker.cache, [])
        #
        #campana, contacto_id, _ = tracker.next()
        #EventoDeContacto.objects.create(
        #    campana_id=campana.id,
        #    contacto_id=contacto_id,
        #    evento=EVENTO_FINALIZADOR)
        #
        #campana, contacto_id, _ = tracker.next()
        #EventoDeContacto.objects.create(
        #    campana_id=campana.id,
        #    contacto_id=contacto_id,
        #    evento=EVENTO_FINALIZADOR)
        #
        #with self.assertRaises(NoMasContactosEnCampana):
        #    tracker.next()


class TestDatosParaRealizarLlamada(FTSenderBaseTest,
                                   PollDaemonTestUtilsMixin):

    def test_generar_variables_de_canal(self):
        campana = self.crear_campana()
        datos_extras = {
            'NOMBRE': 'Juan Perez',
            'FECHA': '25/01/2000',
            'HORA': '12:04',
        }
        dprl = DatosParaRealizarLlamada(campana, 2, '549114444555', 1,
                                        datos_extras)

        variables = dprl.generar_variables_de_canal()

        pprint.pprint(variables)

        self.assertDictEqual(variables, {
            'NOMBRE': 'Juan Perez',
            'FECHA_dia': '25',
            'FECHA_mes': 'enero',
            'FECHA_anio': '2000',
            'HORA_hora': '12',
            'HORA_min': '4',
        })

    @skipIf(True, "Falta implementar sanitizacion de valores")
    def test_generar_variables_de_canal_sanitiza_valores(self):
        campana = self.crear_campana()
        datos_extras = {
            'NOMBRE': 'Juan, Perez # que! lo @ pario',
            'FECHA': '25/01/2000',
            'HORA': '12:04',
        }
        dprl = DatosParaRealizarLlamada(campana, 2, '549114444555', 1,
                                        datos_extras)

        variables = dprl.generar_variables_de_canal()

        pprint.pprint(variables)

        self.assertDictEqual(variables, {
            'NOMBRE': 'Juan Perez que lo pario',
            'FECHA_dia': '25',
            'FECHA_mes': 'enero',
            'FECHA_anio': '2000',
            'HORA_hora': '12',
            'HORA_min': '4',
        })

    def test_generar_variables_de_canal_DNI(self):
        campana = self.crear_campana(columna_extra='DNI')
        datos_extras = {
            'NOMBRE': 'Juan Perez',
            'FECHA': '25/01/2000',
            'HORA': '12:04',
            'DNI': '32540137',
        }
        dprl = DatosParaRealizarLlamada(campana, 2, '549114444555', 1,
                                        datos_extras)

        variables = dprl.generar_variables_de_canal()

        pprint.pprint(variables)

        self.assertDictEqual(variables, {
            'NOMBRE': 'Juan Perez',
            'FECHA_dia': '25',
            'FECHA_mes': 'enero',
            'FECHA_anio': '2000',
            'HORA_hora': '12',
            'HORA_min': '4',
            'DNI': '32540137',
        })

#
# Estos tests controlan la reincidencia, pero no es algo que
# se manejara en esta version
#
#class CampanaTrackerContactosRecientesTests(FTSenderBaseTest):
#    """Chequea que next() no devuelva contactos que hayan
#    sido procesados recientemente
#    """
#
#    def test_1_contacto(self):
#        campana = self.crear_campana_activa(cant_contactos=1,
#            cantidad_canales=99)
#        self.crea_todas_las_actuaciones(campana)
#
#        tracker = CampanaTracker(campana)
#        tracker.fetch_min = 1
#        tracker.fetch_max = 1
#        self.assertEquals(tracker.cache, [])
#
#        ret1 = tracker.next()
#        ret2 = tracker.next()
#        ret3 = tracker.next()
#
#        self.assertEquals(ret1, ret2)
#        self.assertEquals(ret1, ret3)
#        # FIXME: cambiar tracker o scheduler p/q' esto no suceda
#        # El mismo pendiente es devuelto una y otra vez!
#
#        self.fail("IMPLEMENTAR - no se deberian devolver contactos "
#            "que han sido devuelto recientemente")
#
#    def test_2_contactos(self):
#        campana = self.crear_campana_activa(cant_contactos=2,
#            cantidad_canales=99)
#        self.crea_todas_las_actuaciones(campana)
#
#        tracker = CampanaTracker(campana)
#        tracker.fetch_min = 2
#        tracker.fetch_max = 2
#        self.assertEquals(tracker.cache, [])
#
#        ret1 = tracker.next()
#        ret2 = tracker.next()
#        ret3 = tracker.next()
#        ret4 = tracker.next()
#
#        self.assertNotEqual(ret1, ret2)
#        self.assertNotEqual(ret3, ret4)
#
#        if ret1 == ret3:
#            self.assertEquals(ret1, ret3)
#            self.assertEquals(ret2, ret4)
#        else:
#            self.assertEquals(ret1, ret4)
#            self.assertEquals(ret2, ret3)
#        # FIXME: cambiar tracker o scheduler p/q' esto no suceda
#        # El mismo pendiente es devuelto una y otra vez!
#
#        self.fail("IMPLEMENTAR - no se deberian devolver contactos "
#            "que han sido devuelto recientemente")
