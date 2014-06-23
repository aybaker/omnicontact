# -*- coding: utf-8 -*-

"""Tests generales"""
from __future__ import unicode_literals

import os
import shutil
import datetime
import csv

from django.conf import settings

from django.core.urlresolvers import reverse
from django.db import IntegrityError
from django.test.client import Client
from django.test.utils import override_settings
from django.utils.unittest.case import skipUnless

from fts_daemon.models import EventoDeContacto
from fts_web.models import (AgenteGrupoAtencion, AgregacionDeEventoDeContacto,
    BaseDatosContacto, Campana, Contacto, Opcion, Calificacion, Actuacion)
from fts_web.tests.utiles import FTSenderBaseTest, \
    default_db_is_postgresql
from fts_web.parser import autodetectar_parser
from fts_web.errors import (FtsRecicladoCampanaError, 
    FtsRecicladoBaseDatosContactoError)


class GrupoAtencionTest(FTSenderBaseTest):
    """Clase para testear GrupoAtencion"""

    def test_get_cantidad_agentes(self):
        ga = self.crear_grupo_atencion()
        self.assertEqual(ga.get_cantidad_agentes(), 0)
        AgenteGrupoAtencion.objects.create(
            numero_interno=123, grupo_atencion=ga)
        self.assertEqual(ga.get_cantidad_agentes(), 1)

    def test_get_ring_strategy(self):
        ga = self.crear_grupo_atencion()
        self.assertEqual(ga.get_ring_strategy_display(), "RINGALL")


class BaseDatosContactoTest(FTSenderBaseTest):
    """Clase para testear Base Datos Contacto"""

    def test_obtener_definidas(self):
        """
        Testea el método obtener_definidas().
        """
        bd_contacto = BaseDatosContacto.objects.create(
            nombre="base-datos-contactos",
            archivo_importacion=self.get_test_resource(
                "planilla-ejemplo-0.xls"),
            nombre_archivo_importacion='planilla-ejemplo-0.xls',
            columna_datos=0
        )

        # Verifica que al crear una BaseDatosContacto y no definirla
        # el método no retorne la misma.
        self.assertEqual(BaseDatosContacto.objects.obtener_definidas().count(),
            0)

        # Verifica que la BaseDatosContacto al definirla el método la
        # retorne.
        bd_contacto.define()
        self.assertEqual(BaseDatosContacto.objects.obtener_definidas().count(),
            1)

    def test_define(self):
        """
        Testea el método define()
        """
        bd_contacto = BaseDatosContacto.objects.create(
            nombre="base-datos-contactos",
            archivo_importacion=self.get_test_resource(
                "planilla-ejemplo-0.xls"),
            nombre_archivo_importacion='planilla-ejemplo-0.xls',
            columna_datos=0
        )

        # Verifica que al crear una BaseDatosContacto y no definirla
        # el estado sea sin definir.
        self.assertTrue(bd_contacto.sin_definir)

        # Verifica que la BaseDatosContacto al definirla cambie su
        # estado a definida.
        bd_contacto.define()
        self.assertFalse(bd_contacto.sin_definir)

    tmp = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    MEDIA_ROOT = os.path.join(tmp, "test")

    @override_settings(MEDIA_ROOT=MEDIA_ROOT)
    def test_get_cantidad_contactos(self):
        """
        Testea el método get_cantidad_contactos().
        Procesa la planilla planilla-ejemplo-0.xls que es sabido que
        tiene 6 contactos válidos, y que los datos estan en la columna 0.
        """
        bd_contacto = BaseDatosContacto.objects.create(
            nombre="base-datos-contactos",
            archivo_importacion=self.get_test_resource(
                "planilla-ejemplo-0.xls"),
            nombre_archivo_importacion='planilla-ejemplo-0.xls',
            columna_datos=0
        )
        self.assertEqual(bd_contacto.get_cantidad_contactos(), 0)

        parser = autodetectar_parser(bd_contacto.nombre_archivo_importacion)
        bd_contacto.importa_contactos(parser)

        self.assertEqual(bd_contacto.get_cantidad_contactos(), 6)

    def test_reciclar_base_datos_total(self):
        campana = self._crea_campana_emula_procesamiento()

        bd_contacto_reciclada = BaseDatosContacto.objects.reciclar_base_datos(
            campana.pk, Campana.TIPO_RECICLADO_TOTAL)

        # Verificamos que para TIPO_RECICLADO_TOTAL la base de datos sea la
        # misma.
        self.assertEqual(bd_contacto_reciclada.pk, campana.bd_contacto.pk)

    def test_reciclar_base_datos_pendientes_sin_contactos(self):
        campana = self.crear_campana()

        # Verificamos que para TIPO_RECICLADO_PENDIENTES y sin contactos en
        # EDC, se genere la excepción FtsRecicladoBaseDatosContactoError.

        with self.assertRaises(FtsRecicladoBaseDatosContactoError):
            BaseDatosContacto.objects.reciclar_base_datos(campana.pk,
                Campana.TIPO_RECICLADO_PENDIENTES)

    def test_reciclar_base_datos_pendientes(self):
        campana = self._crea_campana_emula_procesamiento()

        bd_contacto_reciclada = BaseDatosContacto.objects.reciclar_base_datos(
            campana.pk, Campana.TIPO_RECICLADO_PENDIENTES)

        # Verificamos que para TIPO_RECICLADO_PENDIENTES no se la misma 
        # base de datos, que se haya generado una nueva con el reciclado.

        self.assertFalse(bd_contacto_reciclada == campana.bd_contacto)
        self.assertEqual(bd_contacto_reciclada.cantidad_contactos, 
            Contacto.objects.filter(bd_contacto=bd_contacto_reciclada).count())

    def test_campana_obtener_detalle_opciones_seleccionadas(self):
        campana = self._crea_campana_emula_procesamiento()

        detalle_opciones = campana.obtener_detalle_opciones_seleccionadas()
        self.assertTrue(len(detalle_opciones))
        for detalle_opcion in detalle_opciones:
            self.assertIn(type(detalle_opcion[0]), [int, Opcion])
            self.assertTrue(len(detalle_opcion[1]))


class CampanaTest(FTSenderBaseTest):
    """Clase para testear Campana y CampanaManager"""

    def test_campanas_creadas(self):
        """
        - Campana creadas.
        """
        [self.crear_campana() for _ in range(0, 10)]
        self.assertEqual(Campana.objects.all().count(), 10)

    def test_campanas_datos_basicos(self):
        """
        - Datos Básicos de la campana.
        """
        fecha_actual = datetime.date.today()

        #Testeamos que con las fechas correctas se cree la campana.
        fecha_inicio = fecha_actual
        fecha_fin = fecha_actual + datetime.timedelta(days=10)
        self.crear_campana(fecha_inicio, fecha_fin)
        self.assertEqual(Campana.objects.all().count(), 1)

        #Testeamos que con la fecha inicio sea >= a la fecha actual.
        #*** Este Test no debería fallar. Ver validación en modelos***
        #Referencia FTS-86
        fecha_inicio = fecha_actual - datetime.timedelta(days=10)
        fecha_fin = fecha_actual + datetime.timedelta(days=10)
        self.crear_campana(fecha_inicio, fecha_fin)
        #self.assertEqual(Campana.objects.all().count(), 1)

        #Testeamos que con la fecha inicio sea <= a la fecha fin.
        #*** Este Test no debería fallar. Ver validación en modelos***
        #Referencia FTS-86
        fecha_inicio = fecha_actual + datetime.timedelta(days=10)
        fecha_fin = fecha_actual
        self.crear_campana(fecha_inicio, fecha_fin)
        #self.assertEqual(Campana.objects.all().count(), 1)

        #Testeamos que la validación en clean de Campana valide que la cantidad
        #de canales sea menor que la cantidad de contactos de la base de datos.
        #*** Este Test no debería fallar. Ver validación en modelos***
        #Referencia FTS-85
        # FIXME: Por ahora sale el assert puesto en el metodo crear_campaan de
        # utiles.py, debería validar el modelo.
        #self.crear_campana(cant_contactos=1)
        #self.assertEqual(Campana.objects.all().count(), 1)

    def test_campana_opcion(self):
        """
        Opciones creadas a una campana.
        """
        campana = self.crear_campana()
        [self.crea_campana_opcion(digito, campana) for digito in range(0, 5)]
        self.assertEqual(Opcion.objects.all().count(), 5)

    def test_campana_opcion_unique_together(self):
        """
        Opciones creadas a una campana sean
        únicos.
        """

        #Testeamos que no se cree dos opciones con
        #el mismo dígito.
        campana = self.crear_campana()
        self.crea_campana_opcion(0, campana)
        with self.assertRaises(IntegrityError):
            self.crea_campana_opcion(0, campana)

    def test_campana_opcion_unique_together_2(self):
        """
        Opciones creadas a una campana sean
        únicos.
        """
        campana = self.crear_campana()

        #Testeamos que no se cree dos opciones con la misma acción.
        #1- Mismo Grupo de Atención.
        grupo_atencion = self.crear_grupo_atencion()
        self.crea_campana_opcion(0, campana, Opcion.DERIVAR, grupo_atencion)
        with self.assertRaises(IntegrityError):
            self.crea_campana_opcion(1, campana, Opcion.DERIVAR,
                grupo_atencion)

    def test_campana_opcion_unique_together_3(self):
        """
        Opciones creadas a una campana sean
        únicos.
        """
        campana = self.crear_campana()
        self.crea_campana_opcion(0, campana)

        #2- Misma Calificación.
        self.crea_calificaciones(campana)
        calificacion = Calificacion.objects.all()[1]
        self.crea_campana_opcion(1, campana, Opcion.CALIFICAR, None,
            calificacion)
        with self.assertRaises(IntegrityError):
            self.crea_campana_opcion(1, campana, Opcion.CALIFICAR,
                None, calificacion)

    def test_campana_actuacion(self):
        """
        Actuaciones creadas a una campana.
        """
        hora_desde = datetime.time(9, 00)
        hora_hasta = datetime.time(18, 00)

        campana = self.crear_campana()
        [self.crea_campana_actuacion(
            dia_semanal, hora_desde, hora_hasta, campana)
            for dia_semanal in range(0, 4)]

        self.assertEqual(Actuacion.objects.all().count(), 4)

        #Testeamos que con la hora_desde sea < a la hora_hasta.
        #*** Este Test no debería fallar. Ver validación en modelos***
        #Referencia FTS-86
        hora_desde = datetime.time(9, 00)
        hora_hasta = datetime.time(8, 00)
        self.crea_campana_actuacion(5, hora_desde, hora_hasta, campana)
        #self.assertEqual(Actuacion.objects.all().count(), 4)

        #Testeamos que no se solapen dos rangos horarios para una
        #misma campaña.
        #*** Este Test no debería fallar. Ver validación en modelos***
        #Referencia FTS-86
        hora_desde = datetime.time(10, 00)
        hora_hasta = datetime.time(17, 00)
        self.crea_campana_actuacion(3, hora_desde, hora_hasta, campana)
        #self.assertEqual(Actuacion.objects.all().count(), 4)

    def test_campana_activar(self):
        """
        - Campana.activar()
        - Campana.objects.obtener_activas()
        """

        campanas = [self.crear_campana() for _ in range(0, 10)]
        campanas[0].activar()
        campanas[1].activar()

        #Testeamos que no se active una activa.
        self.assertRaises(AssertionError, campanas[0].activar)

        campanas[0].pausar()
        #Testeamos que no se active una pausada.
        self.assertRaises(AssertionError, campanas[0].activar)

        campanas[1].finalizar()
        #Testeamos que no se active una finalizada.
        self.assertRaises(AssertionError, campanas[1].activar)

        #Testeamos que obtener_activas me devuelva las 2 activas solo.
        campanas[2].activar()
        campanas[3].activar()
        campanas_activas = Campana.objects.obtener_activas()
        for c in campanas[2:3]:
            self.assertIn(c, campanas_activas)

    def test_campana_pausar(self):
        """
        - Campana.pausar()
        - Campana.objects.obtener_pausadas()
        """

        campanas = [self.crear_campana() for _ in range(0, 10)]
        campanas[0].activar()
        campanas[1].activar()
        campanas[2].activar()
        campanas[0].pausar()
        campanas[1].pausar()

        #Testeamos que no se pause una pausada.
        self.assertRaises(AssertionError, campanas[0].pausar)

        #Testeamos que no se active con el activar() una pausada.
        self.assertRaises(AssertionError, campanas[0].activar)

        campanas[2].finalizar()
        #Testeamos que no se pause una finalizada.
        self.assertRaises(AssertionError, campanas[2].pausar)

        #Testeamos que no se pause una que no esta activa.
        self.assertRaises(AssertionError, campanas[9].pausar)

        #Testeamos que obtener_pausadas me devuelva las 2 pausadas solo.
        campanas_pausadas = Campana.objects.obtener_pausadas()
        for c in campanas[:2]:
            self.assertIn(c, campanas_pausadas)

    def test_campana_despausar(self):
        """
        - Campana.despausar()
        """

        campanas = [self.crear_campana() for _ in range(0, 10)]
        campanas[0].activar()
        campanas[1].activar()
        campanas[2].activar()
        campanas[1].pausar()
        campanas[2].pausar()

        #Testeamos que no se despause una activa.
        self.assertRaises(AssertionError, campanas[0].despausar)

        #Testeamos que se despause una pausada.
        campanas[1].despausar()
        self.assertEqual(campanas[1].estado, Campana.ESTADO_ACTIVA)

        #Testeamos que no se despause una finalizada.
        campanas[2].finalizar()
        self.assertRaises(AssertionError, campanas[2].despausar)

        #Testeamos que no se despause una que no esta activa.
        self.assertRaises(AssertionError, campanas[9].despausar)

    def test_campana_finalizar(self):
        """Testea:
        - Campana.finalizar()
        - Campana.objects.obtener_finalizadas()
        """

        campanas = [self.crear_campana() for _ in range(0, 10)]
        campanas[0].activar()
        campanas[1].activar()
        campanas[2].activar()

        #Testeamos que no se finalice una en finalizada.
        campanas[0].finalizar()
        self.assertRaises(AssertionError, campanas[0].finalizar)
        self.assertEqual(campanas[0].estado, Campana.ESTADO_FINALIZADA)

        #Testeamos que se finalice una pausada.
        campanas[1].pausar()
        campanas[1].finalizar()
        self.assertEqual(campanas[1].estado, Campana.ESTADO_FINALIZADA)

        #Testeamos que no se finalice una que no esta activa.
        self.assertRaises(AssertionError, campanas[9].pausar)

        #Testeamos que obtener_pausadas me devuelva las 2 pausadas solo.
        campanas_finalizadas = Campana.objects.obtener_finalizadas()
        for c in campanas[:2]:
            self.assertIn(c, campanas_finalizadas)

    def test_campana_obtener_actuacion_actual(self):
        """
        Testea el método obtener_actuacion_actual()
        """
        hoy_ahora = datetime.datetime.today()
        dia_semanal = hoy_ahora.weekday()

        #Establece horario desde y hasta para la actuación en este
        #momento.
        hoy_ahora_menos_1h = hoy_ahora - datetime.timedelta(hours=1)
        hora_desde = datetime.time(
            hoy_ahora_menos_1h.hour, hoy_ahora_menos_1h.minute,
            hoy_ahora_menos_1h.second)
        hoy_ahora_mas_1h = hoy_ahora + datetime.timedelta(hours=1)
        hora_hasta = datetime.time(
            hoy_ahora_mas_1h.hour, hoy_ahora_mas_1h.minute,
            hoy_ahora_mas_1h.second)
        #Crea campaña programada para ejecutarse en este momento.
        campana = self.crear_campana()
        campana.activar()
        actuacion = self.crea_campana_actuacion(
            dia_semanal, hora_desde, hora_hasta, campana)
        #Testea que el método devuelva la actuación creada para este momento.
        self.assertEqual(campana.obtener_actuacion_actual(), actuacion)

        #Establece horario desde y hasta para otra actuación dentro
        #de una hora.
        hoy_ahora_mas_1h = hoy_ahora + datetime.timedelta(hours=1)
        hora_desde = datetime.time(
            hoy_ahora_mas_1h.hour, hoy_ahora_mas_1h.minute,
            hoy_ahora_mas_1h.second)
        hoy_ahora_mas_4h = hoy_ahora + datetime.timedelta(hours=4)
        hora_hasta = datetime.time(
            hoy_ahora_mas_4h.hour, hoy_ahora_mas_4h.minute,
            hoy_ahora_mas_4h.second)
        #Crea campaña programada para ejecutarse en 1 hora.
        self.crea_campana_actuacion(
            dia_semanal, hora_desde, hora_hasta, campana)
        #Testea que el método siga devolviendo solo la primer actuacion creada.
        self.assertEqual(campana.obtener_actuacion_actual(), actuacion)

    def test_campana_verifica_fecha(self):
        """
        Testea el método obtener_actuacion_actual()
        """
        hoy_ahora = datetime.datetime.today()

        campana = self.crear_campana()
        campana.activar()
        #Testeamos que devuelva True para una campaña actual.
        self.assertTrue(campana.verifica_fecha(hoy_ahora))

        manana = hoy_ahora + datetime.timedelta(days=1)
        pasado_manana = hoy_ahora + datetime.timedelta(days=2)
        campana1 = self.crear_campana(manana.date(), pasado_manana.date())
        campana1.activar()
        #Testeamos que devuelva false para una campaña futura.
        self.assertFalse(campana1.verifica_fecha(hoy_ahora))

    def test_campana_obtener_ejecucion(self):
        """
        Testea método obtener_ejecucion.
        """
        hoy_ahora = datetime.datetime.today()
        hora_desde = hoy_ahora - datetime.timedelta(hours=1)
        hora_hasta = hoy_ahora + datetime.timedelta(hours=1)
        dia_semanal = hoy_ahora.weekday()

        #Crea campaña programada para ejecutarse en este momento.
        campana = self.crear_campana()
        self.crea_campana_actuacion(
            dia_semanal, hora_desde, hora_hasta, campana)
        campana.activar()
        #Testea que el método devuelva una campaña y sea la creada.
        campana_ejecucion = Campana.objects.obtener_ejecucion()
        self.assertEquals(campana_ejecucion.count(), 1)
        self.assertEquals(campana_ejecucion[0], campana)

        #Crea otra campaña programada para ejecutarse en este momento.
        campana1 = self.crear_campana()
        self.crea_campana_actuacion(
            dia_semanal, hora_desde, hora_hasta, campana1)
        campana1.activar()
        #Testea que el método devuelva dos campaña y la última sea la creada.
        self.assertEquals(campana_ejecucion.count(), 2)
        self.assertEquals(campana_ejecucion[1], campana1)

        #Crea otra campaña programada para ejecutarse horas antes.
        hora_desde = hoy_ahora - datetime.timedelta(hours=4)
        hora_hasta = hoy_ahora - datetime.timedelta(hours=1)
        campana2 = self.crear_campana()
        self.crea_campana_actuacion(
            dia_semanal, hora_desde, hora_hasta, campana2)
        campana2.activar()
        #Testea que el método siga devolviendo dos campaña y
        #que no esta la última creada en las que devolvió.
        self.assertEquals(campana_ejecucion.count(), 2)
        self.assertNotIn(campana2, campana_ejecucion)

        #Crea otra campaña programada para ejecutarse un día antes
        #y en el mismo rango horario.
        dia_semanal = (hoy_ahora - datetime.timedelta(days=1)).weekday()
        campana3 = self.crear_campana()
        self.crea_campana_actuacion(
            dia_semanal, hora_desde, hora_hasta, campana3)
        campana3.activar()
        #Testea que el método siga devolviendo dos campaña
        # que no esta la última creada en las que devolvió.
        self.assertEquals(campana_ejecucion.count(), 2)
        self.assertNotIn(campana3, campana_ejecucion)

        #Crea campaña programada para ejecutarse en este momento
        #pero no la activa.
        campana4 = self.crear_campana()
        self.crea_campana_actuacion(
            dia_semanal, hora_desde, hora_hasta, campana4)
        #Testea que el método siga devolviendo dos campaña
        # que no esta la última creada en las que devolvió.
        self.assertEquals(campana_ejecucion.count(), 2)
        self.assertNotIn(campana4, campana_ejecucion)

    tmp = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    MEDIA_ROOT = os.path.join(tmp, "test", "reportes")

    @override_settings(MEDIA_ROOT=MEDIA_ROOT)
    def test_campana_exporta_reporte(self):
        import glob

        #Crea y emula procesamiento de campaña.
        campana = self._crea_campana_emula_procesamiento(finaliza=False)

        dirname = 'reporte_campana'
        files_path = "{0}/{1}".format(settings.MEDIA_ROOT, dirname)

        files = glob.glob('{0}/*'.format(files_path))
        for f in files:
            os.remove(f)

        filename = "{0}-reporte.csv".format(campana.id)
        file_path = "{0}/{1}/{2}".format(settings.MEDIA_ROOT, dirname, filename)
        file_url = "{0}/{1}/{2}".format(settings.MEDIA_URL, dirname, filename)

        # Testeo que si la campana no está finalizada de una excepción.
        self.assertRaises(AssertionError, campana.exportar_reporte_csv)

        # Finalizamos la campana, acudimos al método que genera el csv para
        # exportar, validamos que exista el archivo y que el método devuelva
        # la url para accederlo.
        campana.finalizar()
        url_reporte = campana.exportar_reporte_csv()
        self.assertTrue(os.path.exists(file_path))
        self.assertEqual(url_reporte, file_url)

        # Abrimos el archivo y contamos que tenga 100 lineas. Una por contacto,
        # y cada linea con 11 columnas.
        with open(file_path, 'rb') as csvfile:
            reader = csv.reader(csvfile)
            c = 0
            for row in reader:
                self.assertTrue(len(row), 11)
                c += 1
        self.assertEqual(c, 100)

        files = glob.glob('{0}/*'.format(files_path))
        for f in files:
            os.remove(f)

    def test_campana_reciclar_campana(self):
        hora_desde = datetime.time(00, 00)
        hora_hasta = datetime.time(23, 59)

        bd_contacto = self.crear_base_datos_contacto(10)

        campana = self.crear_campana()
        self.crea_calificaciones(campana)
        calificaciones = Calificacion.objects.filter(campana=campana)
        for digito, calificacion in enumerate(calificaciones):
            self.crea_campana_opcion(digito, campana,
                calificacion=calificacion)

        [self.crea_campana_actuacion(dia_semanal, hora_desde, hora_hasta,
            campana) for dia_semanal in range(0, 4)]
        
        campana.activar()

        # Testeamos que no se pueda reciclar una campana que nos este
        # finalizada.
        with self.assertRaises(AssertionError):
            Campana.objects.reciclar_campana(campana.pk, bd_contacto)

        campana.finalizar()
        
        # Testeamos que devuelva error si no encuentra la campana.
        with self.assertRaises(FtsRecicladoCampanaError):
            campana_inexistente = 1500
            Campana.objects.reciclar_campana(campana_inexistente, bd_contacto)

        # Reciclamos la campana. Se utiliza la misma base de datos que la
        # original.
        campana_reciclada = Campana.objects.reciclar_campana(campana.pk,
            bd_contacto)

        # Testeamos que la campana esté en definición y tenga los mismos
        # valores que la original.
        self.assertEqual(campana_reciclada.estado,
            Campana.ESTADO_EN_DEFINICION)
        self.assertEqual(Opcion.objects.filter(campana=campana_reciclada)
            .count(), 5)
        self.assertEqual(Calificacion.objects.filter(
            campana=campana_reciclada).count(), calificaciones.count())
        self.assertEqual(Actuacion.objects.filter(campana=campana_reciclada)
            .count(), 4)
        self.assertEqual(campana.audio_original,
            campana_reciclada.audio_original)
        self.assertEqual(campana.audio_asterisk,
            campana_reciclada.audio_asterisk)
        self.assertEqual(campana.cantidad_canales,
            campana_reciclada.cantidad_canales)
        self.assertEqual(campana.cantidad_intentos,
            campana_reciclada.cantidad_intentos)
        self.assertEqual(campana.segundos_ring, 
            campana_reciclada.segundos_ring)
        self.assertFalse(campana.nombre == campana_reciclada.nombre)

    def test_campana_valida_actuaciones(self):
        # Verificamos una campaña válida.
        fecha_inicio = datetime.datetime.today().date()
        fecha_fin = fecha_inicio + datetime.timedelta(days=2)
        dia_semanal = datetime.datetime.today().weekday()
        hora_desde = datetime.datetime.now()
        hora_hasta = hora_desde + datetime.timedelta(hours=1)

        campana_valida = self.crear_campana_activa(fecha_inicio=fecha_inicio,
                                                   fecha_fin=fecha_fin,)
        self.crea_campana_actuacion(
            dia_semanal, hora_desde.time(), hora_hasta.time(), campana_valida)
        self.assertTrue(campana_valida.valida_actuaciones())

        # Verificamos una campaña inválida.
        fecha_inicio = (datetime.datetime.today().date() +
                        datetime.timedelta(days=2))
        fecha_fin = fecha_inicio + datetime.timedelta(days=2)
        dia_semanal = datetime.datetime.today().weekday()
        hora_desde = datetime.datetime.now()
        hora_hasta = hora_desde + datetime.timedelta(hours=1)

        campana_invalida = self.crear_campana_activa(fecha_inicio=fecha_inicio,
                                                     fecha_fin=fecha_fin,)
        self.crea_campana_actuacion(
            dia_semanal, hora_desde.time(), hora_hasta.time(),
            campana_invalida)
        self.assertFalse(campana_invalida.valida_actuaciones())

    def test_campana_obtener_actuaciones_validas(self):
        fecha_inicio = datetime.datetime.today().date()
        fecha_fin = fecha_inicio + datetime.timedelta(days=1)

        campana = self.crear_campana_activa(fecha_inicio=fecha_inicio,
                                            fecha_fin=fecha_fin,)

        hora_desde = datetime.datetime.now() - datetime.timedelta(hours=2)
        hora_hasta = hora_desde + datetime.timedelta(hours=4)

        # Actuación válida.
        dia_semanal = datetime.datetime.today().weekday()
        actuacion1 = self.crea_campana_actuacion(
            dia_semanal, hora_desde.time(), hora_hasta.time(),
            campana)

        # Actuación válida.
        dia_semanal = (datetime.datetime.today() +
                       datetime.timedelta(days=1)).weekday()
        actuacion2 = self.crea_campana_actuacion(
            dia_semanal, hora_desde.time(), hora_hasta.time(),
            campana)

        # Actuación inválida.
        dia_semanal = (datetime.datetime.today() +
                       datetime.timedelta(days=2)).weekday()
        actuacion3 = self.crea_campana_actuacion(
            dia_semanal, hora_desde.time(), hora_hasta.time(),
            campana)

        self.assertEqual(campana.actuaciones.all().count(), 3)
        self.assertEqual(len(campana.obtener_actuaciones_validas()), 2)
        self.assertEquals([actuacion1, actuacion2],
                          campana.obtener_actuaciones_validas())


class FinalizarVencidasTest(FTSenderBaseTest):
    """Clase para testear Campana.finalizar_vencidas()"""

    def test_finaliza_campana_vieja(self):
        bd = self.crear_base_datos_contacto(2)
        campana = self.crear_campana_activa(bd_contactos=bd,
            cantidad_canales=1)
        campana_vieja = self.crear_campana_activa(bd_contactos=bd,
            cantidad_canales=1)
        campana_vieja.fecha_inicio = datetime.datetime(2001, 01, 01).date()
        campana_vieja.fecha_fin = datetime.datetime(2001, 01, 01).date()
        campana_vieja.save()

        # ---

        Campana.objects.finalizar_vencidas()

        campana = Campana.objects.get(pk=campana.id)
        campana_vieja = Campana.objects.get(pk=campana_vieja.id)
        self.assertEquals(campana.estado, Campana.ESTADO_ACTIVA)
        self.assertEquals(campana_vieja.estado, Campana.ESTADO_FINALIZADA)

    def test_finaliza_campana_de_hoy_sin_actuacion(self):
        now = datetime.datetime.now()

        bd = self.crear_base_datos_contacto(2)
        campana = self.crear_campana_activa(bd_contactos=bd,
            cantidad_canales=1)
        campana_vieja = self.crear_campana_activa(bd_contactos=bd,
            cantidad_canales=1)
        campana_vieja.fecha_inicio = datetime.datetime(2001, 01, 01).date()
        campana_vieja.fecha_fin = now.date()
        campana_vieja.save()

        weekday = now.weekday() - 1
        if weekday == -1:
            weekday = 6

        Actuacion.objects.create(campana=campana_vieja,
            dia_semanal=weekday,
            hora_desde=datetime.time(1, 0),
            hora_hasta=datetime.time(2, 0)
        )

        # ---

        Campana.objects.finalizar_vencidas()

        campana = Campana.objects.get(pk=campana.id)
        campana_vieja = Campana.objects.get(pk=campana_vieja.id)
        self.assertEquals(campana.estado, Campana.ESTADO_ACTIVA)
        self.assertEquals(campana_vieja.estado, Campana.ESTADO_FINALIZADA)

    def test_finaliza_campana_de_hoy_con_actuaciones_vencidas(self):
        now = datetime.datetime.now()

        bd = self.crear_base_datos_contacto(2)
        campana = self.crear_campana_activa(bd_contactos=bd,
            cantidad_canales=1)

        campana_vieja = self.crear_campana_activa(bd_contactos=bd,
            cantidad_canales=1)
        campana_vieja.fecha_inicio = datetime.datetime(2001, 01, 01).date()
        campana_vieja.fecha_fin = now.date()
        campana_vieja.save()

        Actuacion.objects.create(campana=campana_vieja,
            dia_semanal=now.weekday(),
            hora_desde=datetime.time(0, 0),
            hora_hasta=datetime.time(0, 1)
        )

        campana2 = self.crear_campana_activa(bd_contactos=bd,
            cantidad_canales=1)
        campana2.fecha_inicio = datetime.datetime(2001, 01, 01).date()
        campana2.fecha_fin = now.date()
        campana2.save()

        Actuacion.objects.create(campana=campana2,
            dia_semanal=now.weekday(),
            hora_desde=datetime.time(23, 58),
            hora_hasta=datetime.time(23, 59)
        )

        # ---

        Campana.objects.finalizar_vencidas()

        campana = Campana.objects.get(pk=campana.id)
        campana2 = Campana.objects.get(pk=campana2.id)
        campana_vieja = Campana.objects.get(pk=campana_vieja.id)
        self.assertEquals(campana.estado, Campana.ESTADO_ACTIVA)
        self.assertEquals(campana2.estado, Campana.ESTADO_ACTIVA)
        self.assertEquals(campana_vieja.estado, Campana.ESTADO_FINALIZADA)


class ActuacionTests(FTSenderBaseTest):
    """Clase para testear Actuacion"""

    def test_verifica_actuacion(self):
        """
        Testea que el método verifica_actuacion()
        """
        hoy_ahora = datetime.datetime.today()
        dia_semanal = hoy_ahora.weekday()

        #Establece horario desde y hasta para la actuación en este
        #momento.
        hoy_ahora_menos_1h = hoy_ahora - datetime.timedelta(hours=1)
        hora_desde = datetime.time(
            hoy_ahora_menos_1h.hour, hoy_ahora_menos_1h.minute,
            hoy_ahora_menos_1h.second)
        hoy_ahora_mas_1h = hoy_ahora + datetime.timedelta(hours=1)
        hora_hasta = datetime.time(
            hoy_ahora_mas_1h.hour, hoy_ahora_mas_1h.minute,
            hoy_ahora_mas_1h.second)
        #Crea campaña programada para ejecutarse en este momento.
        campana = self.crear_campana()
        campana.activar()
        actuacion = self.crea_campana_actuacion(
            dia_semanal, hora_desde, hora_hasta, campana)
        #Testea que el método devuelva True. La campanaña
        #esta en rango de actuación.
        self.assertTrue(actuacion.verifica_actuacion(hoy_ahora))

        #Establece horario desde y hasta para la actuación dentro
        #de una hora.
        hoy_ahora_mas_1h = hoy_ahora + datetime.timedelta(hours=1)
        hora_desde = datetime.time(
            hoy_ahora_mas_1h.hour, hoy_ahora_mas_1h.minute,
            hoy_ahora_mas_1h.second)
        hoy_ahora_mas_4h = hoy_ahora + datetime.timedelta(hours=4)
        hora_hasta = datetime.time(
            hoy_ahora_mas_4h.hour, hoy_ahora_mas_4h.minute,
            hoy_ahora_mas_4h.second)
        #Crea campaña programada para ejecutarse en 1 hora.
        campana1 = self.crear_campana()
        campana1.activar()
        actuacion1 = self.crea_campana_actuacion(
            dia_semanal, hora_desde, hora_hasta, campana1)
        #Testea que el método devuelva False. La campanaña *NO*
        #esta en rango de actuación.
        self.assertFalse(actuacion1.verifica_actuacion(hoy_ahora))

    def test_dia_concuerda(self):
        lunes = datetime.date(2001, 1, 1)
        martes = datetime.date(2001, 1, 2)
        actuacion = Actuacion(dia_semanal=Actuacion.LUNES,
            hora_desde=datetime.time(0, 0),
            hora_hasta=datetime.time(1, 0),
        )
        self.assertTrue(actuacion.dia_concuerda(lunes))
        self.assertFalse(actuacion.dia_concuerda(martes))
        with self.assertRaises(AssertionError):
            actuacion.dia_concuerda(datetime.datetime.now())

    def test_es_anterior_a(self):
        hora_anterior = datetime.datetime(2001, 1, 1, 15, 47, 59)
        hora_en_rango = datetime.datetime(2001, 1, 1, 16, 47, 59)
        hora_posterior = datetime.datetime(2001, 1, 1, 17, 47, 59)
        actuacion = Actuacion(dia_semanal=Actuacion.LUNES,
            hora_desde=datetime.time(16, 0),
            hora_hasta=datetime.time(17, 0),
        )
        self.assertTrue(actuacion.es_anterior_a(hora_posterior.time()))
        self.assertFalse(actuacion.es_anterior_a(hora_en_rango.time()))
        self.assertFalse(actuacion.es_anterior_a(hora_anterior.time()))
        with self.assertRaises(AssertionError):
            actuacion.es_anterior_a(datetime.datetime.now())
        with self.assertRaises(AssertionError):
            actuacion.es_anterior_a(datetime.datetime.now().date())


@skipUnless(default_db_is_postgresql(), "Requiere PostgreSql")
class ReporteTest(FTSenderBaseTest):
    def setUp(self):
        path_graficos = '{0}graficos/'.format(settings.MEDIA_ROOT)
        if os.path.exists(path_graficos):
            shutil.rmtree(path_graficos)

    def test_detalle_reporte_template(self):
        #Crea y emula procesamiento de campaña.
        campana = self._crea_campana_emula_procesamiento()

        # Verificamos template detalle reporte campaña.
        url = reverse('detalle_campana_reporte', kwargs={"pk": campana.pk})
        c = Client()
        response = c.get(url)
        self.assertEqual(response.status_code, 200)

    # def test_obtener_estadistica(self):
    #     #Crea y emula procesamiento de campaña.
    #     campana = self._crea_campana_emula_procesamiento()
    #     #Obtiene las estadisticas de la campana.
    #     estadisticas = campana.obtener_estadisticas()

    #     #Testea los valores devueltos.
    #     self.assertEqual(estadisticas['total_contactos'], 100)
    #     self.assertEqual(estadisticas['cantidad_intentados'], 100)
    #     self.assertEqual(estadisticas['porcentaje_intentados'], 100)
    #     self.assertEqual(estadisticas['cantidad_no_intentados'], 0)
    #     self.assertEqual(estadisticas['porcentaje_no_intentados'], 0.0)

    #     cantidad_pendientes = estadisticas['total_contactos'] -\
    #         (estadisticas['cantidad_contestadas'] +
    #         estadisticas['cantidad_no_contestadas'])
    #     self.assertEqual(estadisticas['cantidad_pendientes'],
    #         cantidad_pendientes)

    #     porcentaje_pendientes = float(100 * cantidad_pendientes /\
    #         estadisticas['total_contactos'])
    #     self.assertEqual(estadisticas['porcentaje_pendientes'],
    #         porcentaje_pendientes)

    #     cantidad_contestadas = estadisticas['total_contactos'] -\
    #         (estadisticas['cantidad_pendientes'] +
    #         estadisticas['cantidad_no_contestadas'])
    #     self.assertEqual(estadisticas['cantidad_contestadas'],
    #         cantidad_contestadas)
    #     porcentaje_contestadas = float(100 * cantidad_contestadas /\
    #         estadisticas['total_contactos'])
    #     self.assertEqual(estadisticas['porcentaje_contestadas'],
    #         porcentaje_contestadas)

    #     cantidad_no_contestadas = estadisticas['total_contactos'] -\
    #         (estadisticas['cantidad_pendientes'] +
    #         estadisticas['cantidad_contestadas'])
    #     self.assertEqual(estadisticas['cantidad_no_contestadas'],
    #         cantidad_no_contestadas)
    #     porcentaje_no_contestadas = float(100 * cantidad_no_contestadas /\
    #         estadisticas['total_contactos'])
    #     self.assertEqual(estadisticas['porcentaje_no_contestadas'],
    #         porcentaje_no_contestadas)

    #     porcentaje_avance = porcentaje_contestadas + porcentaje_no_contestadas
    #     self.assertEqual(estadisticas['porcentaje_avance'],
    #         porcentaje_avance)

    def test_render_grafico_torta_avance_campana(self):
        #Crea y emula procesamiento de campaña.
        campana = self._crea_campana_emula_procesamiento()

        #Obtento el renderizado de gráfico y lo testeo.
        graficos_estadisticas = \
            campana.obtener_estadisticas_render_graficos_supervision()

        self.assertTrue(graficos_estadisticas[
            'torta_opcion_x_porcentaje'].render())
        self.assertEqual(graficos_estadisticas['estadisticas']
            ['total_contactos'], 100)

    # def test__url_grafico(self):
    #     #Crea y emula procesamiento de campaña.
    #     campana = self._crea_campana_emula_procesamiento()

    #     #Obtengo la url del gráfico de torta general y lo verifico.
    #     url = campana.url_grafico_torta
    #     self.assertEqual(url, Campana.URL_GRAFICOS[Campana.TORTA_GENERAL]\
    #         .format(settings.MEDIA_URL, campana.id))

    #     #Obtengo el path del grafico generado y lo borro.
    #     path = Campana.PATH_GRAFICOS[Campana.TORTA_GENERAL]\
    #         .format(settings.MEDIA_ROOT, campana.id)
    #     os.remove(path)
    #     #Obtengo la url, y verifico que me haya devuelto None, ya que no
    #     #existe mas el archivo.
    #     url = campana.url_grafico_torta
    #     self.assertEqual(url, None)

    # def test__genera_graficos_estadisticas(self):
    #     #Creo un campana activa, si datos procesados.
    #     campana = self.crear_campana_activa(cant_contactos=0)
    #     campana.finalizar()

    #     url = campana.url_grafico_torta
    #     self.assertEqual(url, None)

    def test_render_graficos_reporte(self):
        #Crea y emula procesamiento de campaña.
        campana = self._crea_campana_emula_procesamiento()
        graficos = campana.obtener_estadisticas_render_graficos_reportes()

        self.assertTrue(graficos['torta_general'].render())
        self.assertTrue(graficos['torta_opcion_x_porcentaje'].render())
        self.assertTrue(graficos['barra_atendidos_intentos'].render())

    def test_obtener_contadores_por_intento(self):
        #Crea y emula procesamiento de campaña.
        campana = self._crea_campana_emula_procesamiento()
        contadores = EventoDeContacto.objects_estadisticas.\
            obtener_contadores_por_intento(campana.pk,
                campana.cantidad_intentos, None)

        self.assertEqual(len(contadores), 3)
        self.assertEqual(contadores[1]['cantidad_intentos'], 100)

    def test_establecer_agregacion(self):
        #Crea y emula procesamiento de campaña.
        campana = self._crea_campana_emula_procesamiento()
        timestamp_ultimo_evento = EventoDeContacto.objects.filter(
            campana_id=campana.id).latest('timestamp').timestamp
        tipo_agregacion = AgregacionDeEventoDeContacto.TIPO_AGREGACION_REPORTE
        AgregacionDeEventoDeContacto.objects.establece_agregacion(campana.pk,
            campana.cantidad_intentos, tipo_agregacion)
        self.assertEqual(AgregacionDeEventoDeContacto.objects.count(), 3)
        self.assertEqual(AgregacionDeEventoDeContacto.objects.get(
            numero_intento=1).cantidad_intentos, 100)
        self.assertEqual(AgregacionDeEventoDeContacto.objects.get(
            numero_intento=1).timestamp_ultimo_evento, timestamp_ultimo_evento)
        self.assertEqual(AgregacionDeEventoDeContacto.objects.get(
            numero_intento=1).tipo_agregacion, tipo_agregacion)

        #Segundo intento de Agregacion, para verifica que sumarice y no que
        #genere nuevos registros.
        AgregacionDeEventoDeContacto.objects.establece_agregacion(campana.pk,
            campana.cantidad_intentos, tipo_agregacion)
        self.assertEqual(AgregacionDeEventoDeContacto.objects.all().count(), 3)
        self.assertEqual(AgregacionDeEventoDeContacto.objects.get(
            numero_intento=1).cantidad_intentos, 200)
        self.assertEqual(AgregacionDeEventoDeContacto.objects.get(
            numero_intento=1).timestamp_ultimo_evento, timestamp_ultimo_evento)
        self.assertEqual(AgregacionDeEventoDeContacto.objects.get(
            numero_intento=1).tipo_agregacion, tipo_agregacion)

    def test_procesa_agregacion(self):
        #Crea y emula procesamiento de campaña.
        campana = self._crea_campana_emula_procesamiento()
        tipo_agregacion = AgregacionDeEventoDeContacto.TIPO_AGREGACION_REPORTE
        dic_totales = AgregacionDeEventoDeContacto.objects.procesa_agregacion(
            campana.pk, campana.cantidad_intentos, tipo_agregacion)
        self.assertEqual(dic_totales['total_intentados'], 100)
        self.assertEqual(dic_totales['limite_intentos'], 3)
        self.assertEqual(dic_totales['total_contactos'], 100)

        dic_totales = AgregacionDeEventoDeContacto.objects.procesa_agregacion(
            campana.pk, campana.cantidad_intentos, tipo_agregacion)
        self.assertEqual(dic_totales['total_intentados'], 100)
        self.assertEqual(dic_totales['limite_intentos'], 3)
        self.assertEqual(dic_totales['total_contactos'], 100)


        # print "# procesa_agregacion() #"
        # import pprint
        # pp = pprint.PrettyPrinter(indent=4)
        # data = AgregacionDeEventoDeContacto.objects.procesa_agregacion(
        #     campana.pk)
        # pp.pprint(data)
