# -*- coding: utf-8 -*-

"""Unittests del modelo Campana"""

from __future__ import unicode_literals

import datetime

from django.utils.unittest.case import skipIf
from fts_web.models import (Campana, Actuacion, GrupoAtencion,
    DerivacionExterna, Opcion, AudioDeCampana)

from fts_web.tests.utiles import FTSenderBaseTest
from fts_web.services.creacion_campana import (
    ActivacionCampanaTemplateService, ValidarCampanaError,
    RestablecerDialplanError)

from mock import Mock, patch


class ObtenerVencidasParaFinalizarTest(FTSenderBaseTest):
    """Clase para testear Campana.objects.obtener_vencidas_para_finalizar()"""

    def test_devuelve_vieja(self):
        """Testea que devuelve campana con fecha_fin pasada"""
        bd = self.crear_base_datos_contacto(2)
        self.crear_campana_activa(bd_contactos=bd, cantidad_canales=1)

        # Campaña vieja, finalizó hace mucho
        campana_vieja = self.crear_campana_activa(bd_contactos=bd,
                                                  cantidad_canales=1)
        campana_vieja.fecha_inicio = datetime.datetime(2001, 01, 01).date()
        campana_vieja.fecha_fin = datetime.datetime(2001, 01, 01).date()
        campana_vieja.save()

        self.assertEquals(Campana.objects.count(), 2)

        # ---

        campanas = list(Campana.objects.obtener_vencidas_para_finalizar())

        self.assertEqual(len(campanas), 1)
        self.assertEqual(campanas[0].id, campana_vieja.id)

    def test_devuelve_de_hoy_sin_actuacion(self):
        now = datetime.datetime.now()

        bd = self.crear_base_datos_contacto(2)
        self.crear_campana_activa(bd_contactos=bd, cantidad_canales=1)

        # Camp. q' finaliza hoy pero NO posee actuacion para hoy
        campana_a_finalizar = self.crear_campana_activa(bd_contactos=bd,
                                                        cantidad_canales=1)
        campana_a_finalizar.fecha_inicio = datetime.datetime(2001, 01, 01).\
            date()
        campana_a_finalizar.fecha_fin = now.date()
        campana_a_finalizar.save()

        weekday = now.weekday() - 1
        if weekday == -1:
            weekday = 6

        Actuacion.objects.create(campana=campana_a_finalizar,
            dia_semanal=weekday,
            hora_desde=datetime.time(1, 0),
            hora_hasta=datetime.time(2, 0)
        )

        self.assertEquals(Campana.objects.count(), 2)

        # ---

        campanas = list(Campana.objects.obtener_vencidas_para_finalizar())

        self.assertEqual(len(campanas), 1)
        self.assertEqual(campanas[0].id, campana_a_finalizar.id)

    def test_devuelve_de_hoy_con_actuaciones_vencidas(self):
        now = datetime.datetime.now()

        bd = self.crear_base_datos_contacto(2)
        self.crear_campana_activa(bd_contactos=bd, cantidad_canales=1)

        # Campaña q' finaliza HOY, con Actuacion para hoy (pero vencida)
        campana_a_finalizar = self.crear_campana_activa(bd_contactos=bd,
                                                        cantidad_canales=1)
        campana_a_finalizar.fecha_inicio = datetime.datetime(2001, 01, 01).\
            date()
        campana_a_finalizar.fecha_fin = now.date()
        campana_a_finalizar.save()

        Actuacion.objects.create(campana=campana_a_finalizar,
            dia_semanal=now.weekday(),
            hora_desde=datetime.time(0, 0),
            hora_hasta=datetime.time(0, 1)
        )

        # Campaña con actuacion! No deberia ser devuelta
        campana_a_ejecutar = self.crear_campana_activa(bd_contactos=bd,
                                                       cantidad_canales=1)
        campana_a_ejecutar.fecha_inicio = datetime.datetime(2001, 01, 01).\
            date()
        campana_a_ejecutar.fecha_fin = now.date()
        campana_a_ejecutar.save()

        Actuacion.objects.create(campana=campana_a_ejecutar,
            dia_semanal=now.weekday(),
            hora_desde=datetime.time(23, 58),
            hora_hasta=datetime.time(23, 59)
        )

        self.assertEquals(Campana.objects.count(), 3)

        # ---

        campanas = list(Campana.objects.obtener_vencidas_para_finalizar())

        self.assertEqual(len(campanas), 1)
        self.assertEqual(campanas[0].id, campana_a_finalizar.id)

    @skipIf(True, "Falta implementar")
    def test_devuelve_de_manana_sin_actuaciones(self):
        # FIXME: implementar tests y funcionalidad!
        pass


class EliminarCampanaTest(FTSenderBaseTest):

    def test_campana_puede_borrarse_falla(self):
        campana = Campana(id=1)
        campana.save = Mock()
        campana.estado = Campana.ESTADO_FINALIZADA

        # -----

        self.assertEqual(campana.puede_borrarse(), False)

    def test_campana_puede_borrarse(self):
        campana = Campana(id=1)
        campana.save = Mock()
        campana.estado = Campana.ESTADO_DEPURADA

        # -----

        self.assertEqual(campana.puede_borrarse(), True)

    def test_campana_borrar_falla_con_estado_finalizada(self):
        campana = Campana(id=1)
        campana.save = Mock()
        campana.estado = Campana.ESTADO_FINALIZADA

        # -----
        self.assertRaises(AssertionError, campana.borrar)

    def test_campana_borrar_con_estado_depurada(self):
        campana = Campana(id=1)
        campana.save = Mock()
        campana.estado = Campana.ESTADO_DEPURADA

        # -----
        campana.borrar()
        self.assertEqual(campana.estado, Campana.ESTADO_BORRADA)

    def test_campana_filtro_de_borradas(self):
        campana = Campana(id=1)
        campana.save = Mock()
        campana.estado = Campana.ESTADO_DEPURADA

        # -----
        campana.borrar()

        with self.assertRaises(Campana.DoesNotExist):
            Campana.objects.get(id=1)


class MetodosValidadoresDeCampanaTest(FTSenderBaseTest):
    def setUp(self):
        AudioDeCampana.objects.all().delete()

    def test_campana_valida_audio_falla_sin_audios_de_campana(self):
        campana = Campana(id=1)
        campana.save = Mock()

        # -----

        self.assertEqual(campana.valida_audio(), False)

    def test_campana_valida_audio_falla_con_audios_sin_un_attr_seteado(self):
        campana = Campana(id=1)
        campana.save = Mock()

        adc = AudioDeCampana(id=1, orden=1, campana=campana)
        adc.save()

        # -----

        self.assertEqual(campana.valida_audio(), False)

    def test_campana_valida_audio(self):
        campana = Campana(id=1)
        campana.save = Mock()

        adc = AudioDeCampana(id=1, orden=1, campana=campana, tts='NOMBRE')
        adc.save()

        # -----

        self.assertEqual(campana.valida_audio(), True)

    def test_campana_valida_estado_en_definicion_falla(self):
        campana = Campana(id=1)
        campana.save = Mock()
        campana.estado = Campana.ESTADO_ACTIVA

        # -----

        self.assertEqual(campana.valida_estado_en_definicion(), False)

    def test_campana_valida_estado_en_definicion(self):
        campana = Campana(id=1)
        campana.save = Mock()
        campana.estado = Campana.ESTADO_EN_DEFINICION

        # -----

        self.assertEqual(campana.valida_estado_en_definicion(), True)

    def test_campana_valida_grupo_atencion(self):
        grupo_atencion = self.crear_grupo_atencion()

        campana = Campana(id=1)
        campana.save = Mock()

        self.crea_campana_opcion(0, campana,
                                 accion=Opcion.DERIVAR_GRUPO_ATENCION,
                                 grupo_atencion=grupo_atencion)

        # -----

        self.assertEqual(campana.valida_grupo_atencion(), True)

    def test_campana_valida_grupo_atencion_falla(self):
        grupo_atencion = self.crear_grupo_atencion()
        grupo_atencion.borrar()

        campana = Campana(id=1)
        campana.save = Mock()

        self.crea_campana_opcion(0, campana,
                                 accion=Opcion.DERIVAR_GRUPO_ATENCION,
                                 grupo_atencion=grupo_atencion)

        # -----

        self.assertEqual(campana.valida_grupo_atencion(), False)

    def test_campana_valida_derivacion_externa(self):
        derivacion_externa = self.crear_derivacion_externa()

        campana = Campana(id=1)
        campana.save = Mock()

        self.crea_campana_opcion(0, campana,
                                 accion=Opcion.DERIVAR_DERIVACION_EXTERNA,
                                 derivacion_externa=derivacion_externa)

        # -----

        self.assertEqual(campana.valida_derivacion_externa(), True)

    def test_campana_valida_derivacion_externa_falla(self):
        derivacion_externa = self.crear_derivacion_externa()
        derivacion_externa.borrar()

        campana = Campana(id=1)
        campana.save = Mock()

        self.crea_campana_opcion(0, campana,
                                 accion=Opcion.DERIVAR_DERIVACION_EXTERNA,
                                 derivacion_externa=derivacion_externa)

        # -----

        self.assertEqual(campana.valida_derivacion_externa(), False)

    def test_campana_valida_tts_falla_tts_no_en_base_datos(self):
        campana = self.crear_campana_activa()

        adc = AudioDeCampana.objects.create(orden=6, campana=campana,
                                            tts='ESTE_NO_ESTA_EN_BDC')
        adc.save()

        # -----

        self.assertEqual(campana.valida_tts(), False)

    def test_campana_valida_tts_no_falla(self):
        campana = self.crear_campana_activa()

        # -----

        self.assertEqual(campana.valida_tts(), True)


class TemplatesObtieneActivosActivaTemplateTest(FTSenderBaseTest):

    def test_devuelve_1_activo(self):
        campana1 = self.crear_campana()
        campana1.es_template = True
        campana1.estado = Campana.ESTADO_TEMPLATE_EN_DEFINICION
        campana1.save()

        campana2 = self.crear_campana()
        campana2.es_template = True
        campana2.estado = Campana.ESTADO_TEMPLATE_ACTIVO
        campana2.save()

        # -----

        templates_activos = \
            list(Campana.objects_template.obtener_activos())
        self.assertEqual(len(templates_activos), 1)
        self.assertEqual(templates_activos[0], campana2)

    def test_no_devuelve_activo(self):
        campana1 = self.crear_campana()
        campana1.es_template = True
        campana1.estado = Campana.ESTADO_TEMPLATE_EN_DEFINICION
        campana1.save()

        # -----

        templates_activos = \
            list(Campana.objects_template.obtener_activos())
        self.assertEqual(len(templates_activos), 0)

    def test_activar_template_falla(self):
        campana1 = self.crear_campana()
        campana1.es_template = True
        campana1.estado = Campana.ESTADO_TEMPLATE_ACTIVO
        campana1.save()

        # -----

        with self.assertRaises(AssertionError):
            campana1.activar_template()

    def test_activar_template_no_falla(self):
        campana1 = self.crear_campana()
        campana1.es_template = True
        campana1.estado = Campana.ESTADO_TEMPLATE_EN_DEFINICION
        campana1.save()

        # -----

        campana1.activar_template()
        self.assertEqual(campana1.estado, Campana.ESTADO_TEMPLATE_ACTIVO)


class TemplatesDeleteTest(FTSenderBaseTest):

    def test_borrar_template_falla_estado_incorrecto(self):
        campana1 = self.crear_campana()
        campana1.es_template = True
        campana1.estado = Campana.ESTADO_TEMPLATE_EN_DEFINICION
        campana1.save()

        # -----

        with self.assertRaises(AssertionError):
            campana1.borrar_template()

    def test_borrar_template_no_falla(self):
        campana1 = self.crear_campana()
        campana1.es_template = True
        campana1.estado = Campana.ESTADO_TEMPLATE_ACTIVO
        campana1.save()

        # -----

        campana1.borrar_template()
        self.assertEqual(campana1.estado, Campana.ESTADO_BORRADA)


class TemplatesCreaCampanaDeTemplate(FTSenderBaseTest):
    def test_falla_estado_incorrecto(self):
        template = Campana(pk=1)
        template.es_template = True
        template.estado = Campana.ESTADO_TEMPLATE_EN_DEFINICION

        # -----

        with self.assertRaises(AssertionError):
            Campana.objects_template.crea_campana_de_template(template)

    def test_falla_no_es_template(self):
        template = Campana(pk=1)
        template.es_template = False
        template.estado = Campana.ESTADO_TEMPLATE_ACTIVO

        # -----

        with self.assertRaises(AssertionError):
            Campana.objects_template.crea_campana_de_template(template)

    def test_no_falla(self):
        hora_desde = datetime.time(00, 00)
        hora_hasta = datetime.time(23, 59)

        template = self.crear_campana()
        self.crea_calificaciones(template)
        self.crea_todas_las_opcion_posibles(template)

        [self.crea_campana_actuacion(dia_semanal, hora_desde, hora_hasta,
            template) for dia_semanal in range(0, 4)]
        template.es_template = True
        template.estado = Campana.ESTADO_TEMPLATE_ACTIVO

        # -----

        campana = Campana.objects_template.crea_campana_de_template(template)


class CampanaReplicarCampana(FTSenderBaseTest):
    def test_replicar_campana_falla_parametro_incorrecto(self):
        campana = Opcion(pk=1)

        # -----

        with self.assertRaises(AssertionError):
            Campana.objects.replicar_campana(campana)

    def test_replicar_campana_no_falla(self):
        hora_desde = datetime.time(00, 00)
        hora_hasta = datetime.time(23, 59)

        campana = self.crear_campana()
        self.crea_calificaciones(campana)
        self.crea_todas_las_opcion_posibles(campana)

        [self.crea_campana_actuacion(dia_semanal, hora_desde, hora_hasta,
            campana) for dia_semanal in range(0, 4)]

        campana.activar()

        # -----

        campana_replicada = Campana.objects.replicar_campana(campana)

        self.assertEqual(campana_replicada.estado,
                         Campana.ESTADO_EN_DEFINICION)
        self.assertEqual(Opcion.objects.filter(
                         campana=campana_replicada).count(), 8)
        self.assertEqual(Actuacion.objects.filter(
                         campana=campana_replicada).count(), 4)
        self.assertEqual(campana.cantidad_canales,
                         campana_replicada.cantidad_canales)
        self.assertEqual(campana.cantidad_intentos,
                         campana_replicada.cantidad_intentos)
        self.assertEqual(campana.segundos_ring,
                         campana_replicada.segundos_ring)
        self.assertEqual(AudioDeCampana.objects.filter(
                         campana=campana_replicada).count(), 5)


class ValidarCampanaTest(FTSenderBaseTest):
    """
    Este test corresponde al método _validar_campana del servicio
    ActivacionCampanaTemplateService.
    """

    def test_validar_campana_no_falla(self):
        campana = self.crear_campana_activa()

        campana.bd_contacto.verifica_depurada = Mock(return_value=False)
        campana.valida_audio = Mock(return_value=True)
        campana.valida_grupo_atencion = Mock(return_value=True)
        campana.valida_derivacion_externa = Mock(return_value=True)
        campana.valida_tts = Mock(return_value=True)

        # -----

        activacion_campana_service = ActivacionCampanaTemplateService()
        activacion_campana_service._validar_campana(campana)

    def test_validar_campana_falla_bd_depurada(self):
        campana = self.crear_campana_activa()

        campana.bd_contacto.verifica_depurada = Mock(return_value=True)
        campana.valida_audio = Mock(return_value=True)
        campana.valida_grupo_atencion = Mock(return_value=True)
        campana.valida_derivacion_externa = Mock(return_value=True)
        campana.valida_tts = Mock(return_value=True)

        # -----

        activacion_campana_service = ActivacionCampanaTemplateService()

        with self.assertRaises(ValidarCampanaError):
            activacion_campana_service._validar_bd_contacto_campana(campana)

    def test_validar_campana_falla_audio_invalido(self):
        campana = self.crear_campana_activa()

        campana.bd_contacto.verifica_depurada = Mock(return_value=False)
        campana.valida_audio = Mock(return_value=False)
        campana.valida_grupo_atencion = Mock(return_value=True)
        campana.valida_derivacion_externa = Mock(return_value=True)
        campana.valida_tts = Mock(return_value=True)

        # -----

        activacion_campana_service = ActivacionCampanaTemplateService()

        with self.assertRaises(ValidarCampanaError):
            activacion_campana_service._validar_campana(campana)

    def test_validar_campana_falla_grupo_atencion_invalido(self):
        campana = self.crear_campana_activa()

        campana.bd_contacto.verifica_depurada = Mock(return_value=False)
        campana.valida_audio = Mock(return_value=True)
        campana.valida_grupo_atencion = Mock(return_value=False)
        campana.valida_derivacion_externa = Mock(return_value=True)
        campana.valida_tts = Mock(return_value=True)

        # -----

        activacion_campana_service = ActivacionCampanaTemplateService()

        with self.assertRaises(ValidarCampanaError):
            activacion_campana_service._validar_campana(campana)

    def test_validar_campana_falla_derivacion_externa_invalido(self):
        campana = self.crear_campana_activa()

        campana.bd_contacto.verifica_depurada = Mock(return_value=False)
        campana.valida_audio = Mock(return_value=True)
        campana.valida_grupo_atencion = Mock(return_value=True)
        campana.valida_derivacion_externa = Mock(return_value=False)
        campana.valida_tts = Mock(return_value=True)

        # -----

        activacion_campana_service = ActivacionCampanaTemplateService()

        with self.assertRaises(ValidarCampanaError):
            activacion_campana_service._validar_campana(campana)

    def test_validar_campana_falla_tts_invalido(self):
        campana = self.crear_campana_activa()

        campana.bd_contacto.verifica_depurada = Mock(return_value=False)
        campana.valida_audio = Mock(return_value=True)
        campana.valida_grupo_atencion = Mock(return_value=True)
        campana.valida_derivacion_externa = Mock(return_value=True)
        campana.valida_tts = Mock(return_value=False)

        # -----

        activacion_campana_service = ActivacionCampanaTemplateService()

        with self.assertRaises(ValidarCampanaError):
            activacion_campana_service._validar_bd_contacto_campana(campana)


class ValidarActuacionCampanaTest(FTSenderBaseTest):
    """
    Este test corresponde al método _validar_actuacion_campana del servicio
    ActivacionCampanaTemplateService.
    """

    def test_validar_actuacion_campana_no_falla(self):
        campana = self.crear_campana_activa()

        campana.valida_actuaciones = Mock(return_value=True)

        # -----

        activacion_campana_service = ActivacionCampanaTemplateService()
        activacion_campana_service._validar_actuacion_campana(campana)

    def test_validar_actuacion_campana_falla_bd_depurada(self):
        campana = self.crear_campana_activa()

        campana.valida_actuaciones = Mock(return_value=False)

        # -----

        activacion_campana_service = ActivacionCampanaTemplateService()

        with self.assertRaises(ValidarCampanaError):
            activacion_campana_service._validar_actuacion_campana(campana)


class ActivarCampanaTest(FTSenderBaseTest):
    """
    Este test corresponde al método activar del servicio
    ActivacionCampanaTemplateService.
    """

    def test_activar_campana_no_falla(self):
        campana = self.crear_campana()

        activacion_campana_service = ActivacionCampanaTemplateService()
        activacion_campana_service._validar_campana = Mock()
        activacion_campana_service._validar_actuacion_campana = Mock()
        activacion_campana_service._generar_y_recargar_configuracion_asterisk = Mock()

        # -----

        activacion_campana_service.activar(campana)
        self.assertEqual(campana.estado, Campana.ESTADO_ACTIVA)

    def test_activar_campana_falla_validacion_no_se_activa(self):
        campana = self.crear_campana()

        activacion_campana_service = ActivacionCampanaTemplateService()
        activacion_campana_service._validar_campana = Mock(
            side_effect=ValidarCampanaError())
        activacion_campana_service._validar_actuacion_campana = Mock()
        activacion_campana_service._generar_y_recargar_configuracion_asterisk = Mock()

        # -----

        with self.assertRaises(ValidarCampanaError):
            activacion_campana_service.activar(campana)
        self.assertEqual(campana.estado, Campana.ESTADO_EN_DEFINICION)

    def test_activar_campana_falla_actuacion_no_se_activa(self):
        campana = self.crear_campana()

        activacion_campana_service = ActivacionCampanaTemplateService()
        activacion_campana_service._validar_campana = Mock()
        activacion_campana_service._validar_actuacion_campana = Mock(
            side_effect=ValidarCampanaError())
        activacion_campana_service._generar_y_recargar_configuracion_asterisk = Mock()

        # -----

        with self.assertRaises(ValidarCampanaError):
            activacion_campana_service.activar(campana)
        self.assertEqual(campana.estado, Campana.ESTADO_EN_DEFINICION)

    def test_activar_campana_falla_restablecer_dialplan_se_activa(self):
        campana = self.crear_campana()

        activacion_campana_service = ActivacionCampanaTemplateService()
        activacion_campana_service._validar_campana = Mock()
        activacion_campana_service._validar_actuacion_campana = Mock()
        activacion_campana_service._generar_y_recargar_configuracion_asterisk = Mock(
            side_effect=RestablecerDialplanError())
        # -----

        with self.assertRaises(RestablecerDialplanError):
            activacion_campana_service.activar(campana)
        self.assertEqual(campana.estado, Campana.ESTADO_ACTIVA)

    def test_activar_template_no_falla(self):
        campana = self.crear_campana()
        campana.estado = Campana.ESTADO_TEMPLATE_EN_DEFINICION
        campana.es_template = True
        campana.save()

        activacion_campana_service = ActivacionCampanaTemplateService()
        activacion_campana_service._validar_campana = Mock()

        # -----

        activacion_campana_service.activar(campana)
        self.assertEqual(campana.estado, Campana.ESTADO_TEMPLATE_ACTIVO)

    def test_activar_template_falla_validacion_no_se_activa(self):
        campana = self.crear_campana()
        campana.estado = Campana.ESTADO_TEMPLATE_EN_DEFINICION
        campana.es_template = True
        campana.save()

        activacion_campana_service = ActivacionCampanaTemplateService()
        activacion_campana_service._validar_campana = Mock(
            side_effect=ValidarCampanaError())

        # -----

        with self.assertRaises(ValidarCampanaError):
            activacion_campana_service.activar(campana)
        self.assertEqual(campana.estado, Campana.ESTADO_TEMPLATE_EN_DEFINICION)


class RestablecerDialplanCampanaTest(FTSenderBaseTest):
    """
    Este test corresponde al método _generar_y_recargar_configuracion_asterisk del servicio
    ActivacionCampanaTemplateService.
    """

    def test_restablecer_dialplan_campana_no_falla(self):
        activacion_campana_service = ActivacionCampanaTemplateService()

        activacion_campana_service.dialplan_config_creator.\
            create_dialplan = Mock()
        activacion_campana_service.queue_config_creator.\
            create_queue = Mock()
        activacion_campana_service.reload_asterisk_config.reload_config = \
            Mock(return_value=0)

        # -----

        activacion_campana_service._generar_y_recargar_configuracion_asterisk()

    def test_restablecer_dialplan_campana_falla_dialplan(self):
        activacion_campana_service = ActivacionCampanaTemplateService()

        activacion_campana_service.dialplan_config_creator.\
            create_dialplan = Mock(side_effect=RestablecerDialplanError())
        activacion_campana_service.queue_config_creator.\
            create_queue = Mock()
        activacion_campana_service.reload_asterisk_config.reload_config = \
            Mock(return_value=0)

        # -----

        with self.assertRaises(RestablecerDialplanError):
            activacion_campana_service._generar_y_recargar_configuracion_asterisk()

    def test_restablecer_dialplan_campana_falla_queue(self):
        activacion_campana_service = ActivacionCampanaTemplateService()

        activacion_campana_service.dialplan_config_creator.\
            create_dialplan = Mock()
        activacion_campana_service.queue_config_creator.\
            create_queue = Mock(side_effect=RestablecerDialplanError())
        activacion_campana_service.reload_asterisk_config.reload_config = \
            Mock(return_value=0)

        # -----

        with self.assertRaises(RestablecerDialplanError):
            activacion_campana_service._generar_y_recargar_configuracion_asterisk()

    def test_restablecer_dialplan_campana_falla_reload(self):
        activacion_campana_service = ActivacionCampanaTemplateService()

        activacion_campana_service.dialplan_config_creator.\
            create_dialplan = Mock()
        activacion_campana_service.queue_config_creator.\
            create_queue = Mock()
        activacion_campana_service.reload_asterisk_config.reload_config = \
            Mock(side_effect=RestablecerDialplanError())

        # -----

        with self.assertRaises(RestablecerDialplanError):
            activacion_campana_service._generar_y_recargar_configuracion_asterisk()

    def test_restablecer_dialplan_campana_falla_reload_devuelve_1(self):
        activacion_campana_service = ActivacionCampanaTemplateService()

        activacion_campana_service.dialplan_config_creator.\
            create_dialplan = Mock()
        activacion_campana_service.queue_config_creator.\
            create_queue = Mock()
        activacion_campana_service.reload_asterisk_config.reload_config = \
            Mock(return_value=1)

        # -----

        with self.assertRaises(RestablecerDialplanError):
            activacion_campana_service._generar_y_recargar_configuracion_asterisk()