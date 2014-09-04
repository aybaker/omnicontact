# -*- coding: utf-8 -*-

"""
Tests de vistas
"""

from __future__ import unicode_literals

from django.contrib.auth.models import User
from django.core.urlresolvers import reverse

from fts_web.models import Campana
from fts_web.tests.utiles import FTSenderBaseTest


class CampanaCrearTest(FTSenderBaseTest):
    """Testea que las vistas usadas para crear campañas NO puedan ser
    utilizadas con campañas ya definidas
    """

    def setUp(self):
        self.user = User.objects.create_user('user', 'user@e.com', 'user')
        self.assertTrue(self.client.login(username='user', password='user'))
        self.campana = self.crear_campana()
        self.crea_calificaciones(self.campana)
        self.crea_todas_las_opcion_posibles(self.campana)
        self.crea_todas_las_actuaciones(self.campana)

    def test_datos_basicos_campana_lanza_error(self):

        VISTAS = [
            ('datos_basicos_campana', [self.campana.id]),
            ('audio_campana', [self.campana.id]),
            ('calificacion_campana', [self.campana.id]),
            ('calificacion_campana_elimina',
                [self.campana.id, self.campana.calificaciones.all()[0].pk]),
            ('opcion_campana', [self.campana.id]),
            ('opcion_campana_elimina',
                [self.campana.id, self.campana.opciones.all()[0].pk]),
            ('actuacion_campana', [self.campana.id]),
            ('actuacion_campana_elimina',
                [self.campana.id, self.campana.actuaciones.all()[0].pk]),
            ('confirma_campana', [self.campana.id]),
        ]

        for vista, args in VISTAS:
            url = reverse(vista, args=args)
            response = self.client.get(url)
            self.assertEqual(response.status_code, 200, "No se recibio status "
                             "200 al realizar el render inicial de la campana "
                             "en definicion. Vista: {0}. URL: {1}"
                             "".format(vista, url))

        self.campana.activar()

        for url in VISTAS:
            url = reverse(vista, args=args)
            response = self.client.get(url)
            self.assertEqual(response.status_code, 400, "No se recibio status "
                             "400 al realizar el render inicial de la campana "
                             "cuando la campana ya NO ESTA en definicion. "
                             "Vista: {0}. URL: {1}"
                             "".format(vista, url))


class TemplateDeCampanaCrearTest(FTSenderBaseTest):
    """Testea que las vistas usadas para crear templates de campañas NO puedan
    ser utilizadas con templates de campañas ya definidas
    """
    def setUp(self):
        self.user = User.objects.create_user('user', 'user@e.com', 'user')
        self.assertTrue(self.client.login(username='user', password='user'))
        self.campana = self.crear_campana()
        self.campana.estado = Campana.ESTADO_TEMPLATE_EN_DEFINICION
        self.campana.es_template = True
        self.campana.save()

        self.crea_calificaciones(self.campana)
        self.crea_todas_las_opcion_posibles(self.campana)
        self.crea_todas_las_actuaciones(self.campana)

    def test_datos_basicos_campana_lanza_error(self):

        VISTAS = [
            ('datos_basicos_template', [self.campana.id]),
            ('audio_template', [self.campana.id]),
            ('calificacion_template', [self.campana.id]),
            ('calificacion_template_elimina',
                [self.campana.id, self.campana.calificaciones.all()[0].pk]),
            ('opcion_template', [self.campana.id]),
            ('opcion_template_elimina',
                [self.campana.id, self.campana.opciones.all()[0].pk]),
            ('actuacion_template', [self.campana.id]),
            ('actuacion_template_elimina',
                [self.campana.id, self.campana.actuaciones.all()[0].pk]),
            ('confirma_template', [self.campana.id]),
        ]

        for vista, args in VISTAS:
            url = reverse(vista, args=args)
            response = self.client.get(url)
            self.assertEqual(response.status_code, 200, "No se recibio status "
                             "200 al realizar el render inicial de la campana "
                             "en definicion. Vista: {0}. URL: {1}"
                             "".format(vista, url))

        self.campana.activar_template()

        for url in VISTAS:
            url = reverse(vista, args=args)
            response = self.client.get(url)
            self.assertEqual(response.status_code, 400, "No se recibio status "
                             "400 al realizar el render inicial de la campana "
                             "cuando la campana ya NO ESTA en definicion. "
                             "Vista: {0}. URL: {1}"
                             "".format(vista, url))


class ReciclarCampanaTest(FTSenderBaseTest):
    """Testea que las vistas usadas para reciclar campanas NO puedan
    ser utilizadas con campañas ya definidas
    """
    """Testea que las vistas usadas para crear campañas NO puedan ser
    utilizadas con campañas ya definidas
    """

    def setUp(self):
        self.user = User.objects.create_user('user', 'user@e.com', 'user')
        self.assertTrue(self.client.login(username='user', password='user'))

        self.campana = self.crear_campana()
        self.campana.estado = Campana.ESTADO_DEPURADA
        self.campana.save()
        self.crea_calificaciones(self.campana)
        self.crea_todas_las_opcion_posibles(self.campana)
        self.crea_todas_las_actuaciones(self.campana)

        self.campana_reciclada = self.crear_campana()
        self.crea_calificaciones(self.campana_reciclada)
        self.crea_todas_las_opcion_posibles(self.campana_reciclada)
        self.crea_todas_las_actuaciones(self.campana_reciclada)

    def test_datos_basicos_campana_lanza_error(self):

        VISTAS = [
            ('tipo_reciclado_campana', [self.campana.id]),
            ('redefinicion_reciclado_campana', [self.campana_reciclada.id]),
            ('actuacion_reciclado_campana', [self.campana_reciclada.id]),
            ('actuacion_reciclado_campana_elimina',
                [self.campana_reciclada.id,
                 self.campana_reciclada.actuaciones.all()[0].pk]),
            ('confirma_reciclado_campana', [self.campana_reciclada.id]),
        ]

        for vista, args in VISTAS:
            url = reverse(vista, args=args)
            response = self.client.get(url)
            self.assertEqual(response.status_code, 200, "No se recibio status "
                             "200 al realizar el render inicial de la campana "
                             "en definicion. Vista: {0}. URL: {1}"
                             "".format(vista, url))

        self.campana_reciclada.activar()

        for url in VISTAS:
            url = reverse(vista, args=args)
            response = self.client.get(url)
            self.assertEqual(response.status_code, 400, "No se recibio status "
                             "400 al realizar el render inicial de la campana "
                             "cuando la campana ya NO ESTA en definicion. "
                             "Vista: {0}. URL: {1}"
                             "".format(vista, url))


class CrearBaseDeDatosContactosTest(FTSenderBaseTest):
    """Testea que las vistas usadas para crear bd de contactos NO puedan
    ser utilizadas con bd de contactos ya definidas
    """
    pass
