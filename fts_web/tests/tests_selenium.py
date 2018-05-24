# -*- coding: utf-8 -*-

"""Tests generales"""
from __future__ import unicode_literals

import os
import datetime
import logging

from django.core.urlresolvers import reverse
from fts_web.models import Campana, Opcion, \
    Calificacion, Actuacion
from fts_web.tests.utiles import FTSenderBaseTest, FTSenderSeleniumBaseTest
from selenium.webdriver.support.ui import Select


#from django.conf import settings
logger = logging.getLogger(__name__)

if 'SKIP_SELENIUM' not in os.environ:
    print "# Ejecutando test con Selenium"
    print "# Para no ejecutarlos, use:"
    print "    $ SKIP_SELENIUM=1 python manage.py test fts_web"

    class ZBasicUiTests(FTSenderSeleniumBaseTest, FTSenderBaseTest):
        """Clase con tests de UI ejecutados con Selenium

        Como Django ejecuta los tests segun el orden alfabetico del nombre
        de la clase, conviene que esta clase se llame Z(y algo mas) para
        que se ejecuten al final.
        """

        def test_render_grupo_atencion(self):

            # Renderizamos pagina de creacion
            url = reverse('nuevo_grupo_atencion')
            self.render_y_chequear(url)

            grupos = [self.crear_grupo_atencion() for _ in range(0, 4)]

            # Renderizamos pagina de listado
            url = reverse('lista_derivacion')
            self.render_y_chequear(url)
            for ga in grupos:
                self.assertTrueSelenium(
                    self.selenium.page_source.find(ga.nombre) >= 0)

            # Renderizamos pagina de edicion
            for ga in grupos:
                url = reverse('edita_grupo_atencion', kwargs={"pk": ga.id})
                self.render_y_chequear(url)
                self.assertTrueSelenium(
                    self.selenium.page_source.find(ga.nombre) >= 0)

            # El siguiente chequeo va mas alla de lo que tenemos q' hacer
            # (el criterio de aceptacion es testear solo el render de la
            # pagina en Selenium y nada mas), pero lo dejo como referencia
            """Chequeamos q' no aparezcan G.A. eliminados"""
            grupos[0].delete()
            self.render_y_chequear(url)
            self.assertTrueSelenium(
                self.selenium.page_source.find(grupos[0].nombre) == -1)

        def test_render_base_datos_contacto(self):

            # Renderizamos pagina de creacion
            url = reverse('nueva_base_datos_contacto')
            self.render_y_chequear(url)

            #Creamos 4 bases de datos.
            base_datos_contactos = [self.crear_base_datos_contacto(
                numeros_telefonicos=[3513368309, 3518586548])
                for _ in range(0, 4)]

            #Definimo 2 de las bases de datos creadas.
            base_datos_contactos[0].define()
            base_datos_contactos[1].define()

            # Renderizamos pagina de listado
            url = reverse('lista_base_datos_contacto_fts')
            self.render_y_chequear(url)

            #Testeamos que se hayan listado las 2 definidas, y no
            #las dos que no se definieron.
            for i, base_datos_contacto in enumerate(base_datos_contactos):
                if i <= 1:
                    self.assertTrueSelenium(
                        self.selenium.page_source.find(
                            base_datos_contacto.nombre) > 0)
                else:
                    self.assertTrueSelenium(
                        self.selenium.page_source.find(
                            base_datos_contacto.nombre) < 0)

            # # Renderizamos pagina de edicion
            # for base_datos_contacto in base_datos_contactos:
            #     url = reverse('edita_base_datos_contacto',
            #        kwargs={"pk": base_datos_contacto.id})
            #     self.render_y_chequear(url)
            #     self.assertTrueSelenium(
            #        self.selenium.page_source.find(
            #        base_datos_contacto.nombre) >= 0)

        def test_render_campana(self):

            # Renderizamos pagina de creacion
            url = reverse('nueva_campana')
            self.render_y_chequear(url)

            campanas = [self.crear_campana_activa() for _ in range(0, 4)]

            # Renderizamos pagina de listado
            url = reverse('lista_campana')
            self.render_y_chequear(url)
            for campana in campanas:
                self.assertTrueSelenium(
                    self.selenium.page_source.find(campana.nombre) >= 0)

            # # Renderizamos pagina de edicion
            # for campana in campanas:
            #     url = reverse('edita_campana', kwargs={"pk": campana.id})
            #     self.render_y_chequear(url)
            #     self.assertTrueSelenium(self.selenium.page_source.find(
            #        campana.nombre) >= 0)

        def test_render_campana_activa(self):
            #Creamos campana.
            campana = self.crear_campana_activa()

            #Pausamos la campana.
            url = reverse('estado_pausa_campana',
                kwargs={"pk": campana.pk})
            self.render_y_chequear(url)
            campana = Campana.objects.get(pk=campana.pk)

            #Activamos la campana.
            url = reverse('estado_activa_campana',
                kwargs={"pk": campana.pk})
            self.render_y_chequear(url)
            campana = Campana.objects.get(pk=campana.pk)

            self.assertEqual(campana.estado, Campana.ESTADO_ACTIVA)

        def test_render_campana_pausa(self):
            #Creamos campana.
            campana = self.crear_campana_activa()

            #Pausamos la campana.
            url = reverse('estado_pausa_campana',
                kwargs={"pk": campana.pk})
            self.render_y_chequear(url)
            campana = Campana.objects.get(pk=campana.pk)

            self.assertEqual(campana.estado, Campana.ESTADO_PAUSADA)

        def test_render_campana_finalizar(self):
            #Creamos campana y opciones.
            campana = self.crear_campana_activa()

            #Finalizamos la campana.
            url = reverse('estado_finaliza_campana',
                kwargs={"pk": campana.pk})
            self.render_y_chequear(url)
            campana = Campana.objects.get(pk=campana.pk)

            #Chequeamos que no se haya finalizado la campana activa
            self.assertEqual(campana.estado, Campana.ESTADO_ACTIVA)

            #Pausamos la campana.
            url = reverse('estado_pausa_campana',
                kwargs={"pk": campana.pk})
            self.render_y_chequear(url)

            #Finalizamos la campana.
            url = reverse('estado_finaliza_campana',
                kwargs={"pk": campana.pk})
            self.render_y_chequear(url)
            campana = Campana.objects.get(pk=campana.pk)

            #Chequeamos que se haya finalizado la campana pausada.
            self.assertEqual(campana.estado, Campana.ESTADO_FINALIZADA)

        def test_render_submit_campana_audio(self):
            #Testea el paso de audio en el proceso de creación de Campañas.

            campana = self.crear_campana_sin_audio()

            # Renderizamos pagina y verificamos que no se pueda continuar.
            url = reverse('audio_campana', kwargs={"pk": campana.id})
            self.render_y_chequear(url)

            self.assertTrueSelenium(
                self.selenium.page_source.find('Continuar') < 0)

            # Seleccionamos un archivo audio no válido. (mp3) Hacemos el
            # submit y verificamos que NO esté el boton para continuar por
            # no haberse podido convertir el audio.
            self.selenium.find_element_by_id('id_audio_original').send_keys(
                self.get_test_resource("mp3/tribalistas-carnalismo.mp3"))
            form = self.selenium.find_element_by_tag_name('form')
            form.submit()
            self.assertTrueSelenium(
                self.selenium.page_source.find('Continuar') < 0)

            # Seleccionamos un archivo audio válido. (wav) Hacemos el
            # submit y verificamos que esté el boton para continuar.
            self.selenium.find_element_by_id('id_audio_original').send_keys(
                self.get_test_resource("wavs/8k16bitpcm.wav"))
            form = self.selenium.find_element_by_tag_name('form')
            form.submit()
            self.assertTrueSelenium(
                self.selenium.page_source.find('Continuar') > 0)

        def test_render_campana_calificacion(self):

            campana = self.crear_campana()
            self.crea_calificaciones(campana)

            # Renderizamos pagina de creacion
            url = reverse('calificacion_campana', kwargs={"pk": campana.id})
            self.render_y_chequear(url)

        def test_render_campana_calificacion_elimina(self):
            #Testea la eliminación de una Calificación.

            #Creamos campana y calificaciones.
            campana = self.crear_campana()
            self.crea_calificaciones(campana)

            cantidad_inicial_calificaciones = Calificacion.objects.count()
            calificacion_eliminar = Calificacion.objects.all()[1]

            #Renderizamos la pagina de confirmación de eliminación.
            url = reverse('calificacion_campana_elimina',
                kwargs={"pk": calificacion_eliminar.pk})
            self.render_y_chequear(url)

            #Hacemos el submit del form.
            form = self.selenium.find_element_by_tag_name('form')
            form.submit()

            #Verificamos que se haya eliminado.
            self.assertEqual(Calificacion.objects.count(),
                (cantidad_inicial_calificaciones - 1))

            with self.assertRaises(Calificacion.DoesNotExist):
                Calificacion.objects.get(pk=calificacion_eliminar.pk)

        def test_render_campana_opcion(self):

            campana = self.crear_campana()
            [self.crea_campana_opcion(digito, campana)
                for digito in range(0, 5)]

            # Renderizamos pagina de creacion
            url = reverse('opcion_campana', kwargs={"pk": campana.id})
            self.render_y_chequear(url)

        def test_render_campana_opcion_elimina(self):
            #Testea la eliminación de una Opcion.

            #Creamos campana y opciones.
            campana = self.crear_campana()
            [self.crea_campana_opcion(digito, campana)
                for digito in range(0, 5)]

            cantidad_inicial_opciones = Opcion.objects.count()
            opcion_eliminar = Opcion.objects.all()[1]

            #Renderizamos la pagina de confirmación de eliminación.
            url = reverse('opcion_campana_elimina',
                kwargs={"pk": opcion_eliminar.pk})
            self.render_y_chequear(url)

            #Hacemos el submit del form.
            form = self.selenium.find_element_by_tag_name('form')
            form.submit()

            #Verificamos que se haya eliminado.
            self.assertEqual(Opcion.objects.count(),
                (cantidad_inicial_opciones - 1))

            with self.assertRaises(Opcion.DoesNotExist):
                Opcion.objects.get(pk=opcion_eliminar.pk)

        def test_render_campana_actuacion(self):

            hora_desde = datetime.time(9, 00)
            hora_hasta = datetime.time(18, 00)

            campana = self.crear_campana()
            [self.crea_campana_actuacion(
                dia_semanal, hora_desde, hora_hasta, campana)
                for dia_semanal in range(0, 4)]

            # Renderizamos pagina de creacion
            url = reverse('actuacion_campana', kwargs={"pk": campana.id})
            self.render_y_chequear(url)

        def test_render_campana_actuacion_elimina(self):
            #Testea la eliminación de una Actuación.

            #Creamos campana y actuaciones.
            hora_desde = datetime.time(9, 00)
            hora_hasta = datetime.time(18, 00)

            campana = self.crear_campana()
            [self.crea_campana_actuacion(
                dia_semanal, hora_desde, hora_hasta, campana)
                for dia_semanal in range(0, 4)]

            cantidad_inicial_actuaciones = Actuacion.objects.count()
            actuacion_eliminar = Actuacion.objects.all()[1]

            #Renderizamos la pagina de confirmación de eliminación.
            url = reverse('actuacion_campana_elimina',
                kwargs={"pk": actuacion_eliminar.pk})
            self.render_y_chequear(url)

            #Hacemos el submit del form.
            form = self.selenium.find_element_by_tag_name('form')
            form.submit()

            #Verificamos que se haya eliminado.
            self.assertEqual(Actuacion.objects.count(),
                (cantidad_inicial_actuaciones - 1))

            with self.assertRaises(Actuacion.DoesNotExist):
                Actuacion.objects.get(pk=actuacion_eliminar.pk)

        def test_render_campana_confirmar(self):

            hora_desde = datetime.time(9, 00)
            hora_hasta = datetime.time(18, 00)

            campana = self.crear_campana()
            [self.crea_campana_opcion(digito, campana)
                for digito in range(0, 5)]
            [self.crea_campana_actuacion(
                dia_semanal, hora_desde, hora_hasta, campana)
                for dia_semanal in range(0, 4)]

            # Renderizamos pagina de creacion
            url = reverse('confirma_campana', kwargs={"pk": campana.id})
            self.render_y_chequear(url)

        def test_render_campana_detalle(self):

            hora_desde = datetime.time(9, 00)
            hora_hasta = datetime.time(18, 00)

            campana = self.crear_campana()
            [self.crea_campana_opcion(digito, campana)
                for digito in range(0, 5)]
            [self.crea_campana_actuacion(
                dia_semanal, hora_desde, hora_hasta, campana)
                for dia_semanal in range(0, 4)]

            # Renderizamos pagina de detalle
            url = reverse('detalle_campana', kwargs={"pk": campana.id})
            self.render_y_chequear(url)

        def test_render_estados(self):
            #Crea 4 campañas activas, con fecha de inicio actual.
            campanas = [self.crear_campana_activa() for _ in range(0, 4)]

            # Renderizamos pagina de listado
            url = reverse('lista_campana_por_estados')
            self.render_y_chequear(url)

            #Testeamos que no se liste ninguna ya que no
            #están en ejecución porque no tienen actuaciones
            #definidas.
            for campana in campanas:
                self.assertTrueSelenium(
                    self.selenium.page_source.find(campana.nombre) < 0)

            #Creamos actuaciones actuales para las dos primeras campañas.
            dia_semanal = datetime.datetime.today().weekday()
            hora_desde = datetime.datetime.now()
            hora_hasta = hora_desde + datetime.timedelta(hours=1)
            self.crea_campana_actuacion(
                dia_semanal, hora_desde.time(), hora_hasta.time(), campanas[0])
            self.crea_campana_actuacion(
                dia_semanal, hora_desde.time(), hora_hasta.time(), campanas[1])

            # Renderizamos pagina de listado
            url = reverse('lista_campana_por_estados')
            self.render_y_chequear(url)

            #Testeamos que se liste solo las 2 primeras campañas con
            #actuaciones actuales y no las que no tienen actuaciones.
            for i, campana in enumerate(campanas):
                if i <= 1:
                    self.assertTrueSelenium(
                        self.selenium.page_source.find(campana.nombre) > 0)
                else:
                    self.assertTrueSelenium(
                        self.selenium.page_source.find(campana.nombre) < 0)

        def test_render_tipo_reciclado_campana(self):

            #Creamos campana y opciones.
            campana = self.crear_campana_activa()
            campana.pausar()
            campana.finalizar()

            # Renderizamos selección de tipo de reciclado
            url = reverse('tipo_reciclado_campana', kwargs={"pk": campana.id})
            self.render_y_chequear(url)

        def test_render_redefinicion_reciclado_campana(self):
            hora_desde = datetime.time(00, 00)
            hora_hasta = datetime.time(23, 59)

            bd_contacto = self.crear_base_datos_contacto(10)

            campana = self.crear_campana_activa()
            self.crea_calificaciones(campana)
            calificaciones = Calificacion.objects.filter(campana=campana)
            for digito, calificacion in enumerate(calificaciones):
                self.crea_campana_opcion(digito, campana,
                    calificacion=calificacion)
            [self.crea_campana_actuacion(dia_semanal, hora_desde, hora_hasta,
            campana) for dia_semanal in range(0, 4)]

            campana.finalizar()

            # Reciclamos la campana.
            campana_reciclada = Campana.objects.reciclar_campana(campana.pk,
            bd_contacto)


            # Renderizamos selección de tipo de reciclado
            url = reverse('redefinicion_reciclado_campana',
                kwargs={"pk": campana_reciclada.id})
            self.render_y_chequear(url)

        def test_render_actuacion_reciclado_campana(self):

            hora_desde = datetime.time(9, 00)
            hora_hasta = datetime.time(18, 00)

            campana = self.crear_campana()
            [self.crea_campana_actuacion(
                dia_semanal, hora_desde, hora_hasta, campana)
                for dia_semanal in range(0, 4)]

            # Renderizamos pagina de creacion
            url = reverse('actuacion_reciclado_campana',
                kwargs={"pk": campana.id})
            self.render_y_chequear(url)

        def test_render_elimina_actuacion_reciclado_campana(self):
            #Testea la eliminación de una Actuación.

            #Creamos campana y actuaciones.
            hora_desde = datetime.time(9, 00)
            hora_hasta = datetime.time(18, 00)

            campana = self.crear_campana()
            [self.crea_campana_actuacion(
                dia_semanal, hora_desde, hora_hasta, campana)
                for dia_semanal in range(0, 4)]

            cantidad_inicial_actuaciones = Actuacion.objects.count()
            actuacion_eliminar = Actuacion.objects.all()[1]

            #Renderizamos la pagina de confirmación de eliminación.
            url = reverse('actuacion_reciclado_campana_elimina',
                kwargs={"pk": actuacion_eliminar.pk})
            self.render_y_chequear(url)

            #Hacemos el submit del form.
            form = self.selenium.find_element_by_tag_name('form')
            form.submit()

            #Verificamos que se haya eliminado.
            self.assertEqual(Actuacion.objects.count(),
                (cantidad_inicial_actuaciones - 1))

            with self.assertRaises(Actuacion.DoesNotExist):
                Actuacion.objects.get(pk=actuacion_eliminar.pk)

        def test_render_confirma_reciclado_campana(self):
            hora_desde = datetime.time(00, 00)
            hora_hasta = datetime.time(23, 59)

            bd_contacto = self.crear_base_datos_contacto(10)

            campana = self.crear_campana_activa()
            self.crea_calificaciones(campana)
            calificaciones = Calificacion.objects.filter(campana=campana)
            for digito, calificacion in enumerate(calificaciones):
                self.crea_campana_opcion(digito, campana,
                    calificacion=calificacion)
            [self.crea_campana_actuacion(dia_semanal, hora_desde, hora_hasta,
            campana) for dia_semanal in range(0, 4)]

            campana.finalizar()

            # Reciclamos la campana.
            campana_reciclada = Campana.objects.reciclar_campana(campana.pk,
            bd_contacto)


            # Renderizamos selección de tipo de reciclado
            url = reverse('confirma_reciclado_campana',
                kwargs={"pk": campana_reciclada.id})
            self.render_y_chequear(url)

    class ZCargaCampanaTests(FTSenderSeleniumBaseTest, FTSenderBaseTest):

        def test_carga_campana_completa(self):
            """
            Testea la carga de una camaña.
            """

            #Creamos 2 bases de datos.
            base_datos_contactos = [self.crear_base_datos_contacto(
                numeros_telefonicos=[3513368309, 3518586548])
                for _ in range(0, 2)]
            base_datos_contactos[0].define()
            base_datos_contactos[1].define()

            #Creamos 2 grupos atención.
            [self.crear_grupo_atencion() for _ in range(0, 2)]

            fecha_inicio = datetime.date.today()
            fecha_fin = fecha_inicio + datetime.timedelta(days=10)

            #==================================================================
            # Datos Básicos
            #==================================================================
            #Renderizamos la pagina datos básicos.
            url = reverse('nueva_campana')
            self.render_y_chequear(url)

            #Buscamos y seteamos los campos.
            self.selenium.find_element_by_id(
                'id_nombre').send_keys("Test-Carga-Selenium")
            self.selenium.find_element_by_id(
                'id_cantidad_canales').send_keys("1")
            self.selenium.find_element_by_id(
                'id_cantidad_intentos').send_keys("2")
            self.selenium.find_element_by_id(
                'id_segundos_ring').send_keys("10")
            self.selenium.find_element_by_id(
                'id_fecha_inicio').send_keys(fecha_inicio.strftime(
                '%d/%m/%Y'))
            self.selenium.find_element_by_id(
                'id_fecha_fin').send_keys(fecha_fin.strftime(
                '%d/%m/%Y'))
            Select(self.selenium.find_element_by_id(
                'id_bd_contacto')).select_by_index(1)

            #Hacemos click en botón de submit.
            self.selenium.find_element_by_id(
                'id_guardar').click()

            #Verificamos que se haya creado.
            self.assertTrue(Campana.objects.get(nombre='Test-Carga-Selenium'))
            campana = Campana.objects.get(nombre='Test-Carga-Selenium')

            #==================================================================
            # Audio
            #==================================================================
            # Renderizamos pagina de Audio.
            url = reverse('audio_campana', kwargs={"pk": campana.id})
            self.render_y_chequear(url)

            # Seleccionamos un archivo audio válido. (wav)
            self.selenium.find_element_by_id('id_audio_original').send_keys(
                self.get_test_resource("wavs/8k16bitpcm.wav"))

            #Testeamos que no tenga un audio original ni un audio asterisk.
            self.assertFalse(campana.audio_original)
            self.assertFalse(campana.audio_asterisk)

            #Hacemos click en botón de submit.
            self.selenium.find_element_by_id(
                'id_guardar').click()

            #Testeamos que no tenga un audio original ni un audio asterisk.
            campana = Campana.objects.get(nombre='Test-Carga-Selenium')
            self.assertTrue(campana.audio_original)
            self.assertTrue(campana.audio_asterisk)

            #==================================================================
            # Calificaciones
            #==================================================================
            # Renderizamos pagina de Calificaciones.
            url = reverse('calificacion_campana', kwargs={"pk": campana.id})
            self.render_y_chequear(url)

            #Buscamos y seteamos los campos.
            self.selenium.find_element_by_id(
                'id_nombre').send_keys("Excelente-Selenium")

            #Hacemos click en botón de submit.
            self.selenium.find_element_by_id(
                'id_guardar').click()

            #Verificamos que se haya creado.
            self.assertEqual(campana.calificaciones.filter(
                nombre='Excelente-Selenium').count(), 1)

            #==================================================================
            # Opciones
            #==================================================================
            # Renderizamos pagina de Opciones.
            url = reverse('opcion_campana', kwargs={"pk": campana.id})
            self.render_y_chequear(url)

            #Buscamos y seteamos los campos para una accion DERIVAR.
            Select(self.selenium.find_element_by_id(
                'id_digito')).select_by_index(1)
            Select(self.selenium.find_element_by_id(
                'id_accion')).select_by_index(1)
            Select(self.selenium.find_element_by_id(
                'id_grupo_atencion')).select_by_index(1)

            #Hacemos click en botón de submit.
            self.selenium.find_element_by_id(
                'id_guardar').click()

            #Verificamos que se haya creado.
            self.assertEqual(campana.opciones.count(), 1)

            #Buscamos y seteamos los campos para una accion CALIFICAR.
            Select(self.selenium.find_element_by_id(
                'id_digito')).select_by_index(2)
            Select(self.selenium.find_element_by_id(
                'id_accion')).select_by_index(2)
            Select(self.selenium.find_element_by_id(
                'id_calificacion')).select_by_index(1)

            #Hacemos click en botón de submit.
            self.selenium.find_element_by_id(
                'id_guardar').click()

            #Verificamos que se haya creado.
            self.assertEqual(campana.opciones.count(), 2)

            #Buscamos y seteamos los campos para una accion REPETIR.
            Select(self.selenium.find_element_by_id(
                'id_digito')).select_by_index(3)
            Select(self.selenium.find_element_by_id(
                'id_accion')).select_by_index(3)

            #Hacemos click en botón de submit.
            self.selenium.find_element_by_id(
                'id_guardar').click()

            #Verificamos que se haya creado.
            self.assertEqual(campana.opciones.count(), 3)

            #==================================================================
            # Actuaciones
            #==================================================================
            # Renderizamos pagina de Actuacio.
            url = reverse('actuacion_campana', kwargs={"pk": campana.id})
            self.render_y_chequear(url)

            #Buscamos y seteamos los campos.
            Select(self.selenium.find_element_by_id(
                'id_dia_semanal')).select_by_index(1)
            self.selenium.find_element_by_id(
                'id_hora_desde').send_keys("09:10")
            self.selenium.find_element_by_id(
                'id_hora_hasta').send_keys("18:10")

            #Hacemos click en botón de submit.
            self.selenium.find_element_by_id(
                'id_guardar').click()

            #Verificamos que se haya creado.
            self.assertEqual(campana.actuaciones.count(), 1)

            #==================================================================
            # Confirmar
            #==================================================================
            # Renderizamos pagina de Confirmar.
            url = reverse('confirma_campana', kwargs={"pk": campana.id})
            self.render_y_chequear(url)

            self.assertEqual(campana.estado, Campana.ESTADO_EN_DEFINICION)

            #Hacemos click en botón de submit.
            self.selenium.find_element_by_id(
                'submit-id-confirma').click()

            #Verificamos que se haya activado.
            campana = Campana.objects.get(nombre='Test-Carga-Selenium')
            self.assertEqual(campana.estado, Campana.ESTADO_ACTIVA)
