# -*- coding: utf-8 -*-

"""
Tests de vistas
"""

from __future__ import unicode_literals

from django.contrib.auth.models import User
from django.core.files import File
from django.core.urlresolvers import reverse

from fts_web.models import Campana, BaseDatosContacto
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

    def test_creacion_campana(self):

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

    def test_detalle_campana(self):
        VISTAS = [
            ('detalle_campana', [self.campana.id]),
        ]

        for vista, args in VISTAS:
            url = reverse(vista, args=args)
            response = self.client.get(url)
            self.assertEqual(response.status_code, 400, "No se recibio status "
                             "400 al realizar el render del detalle campana "
                             "cuando la campana esta en definicion. "
                             "Vista: {0}. URL: {1}"
                             "".format(vista, url))

        self.campana.activar()

        for url in VISTAS:
            url = reverse(vista, args=args)
            response = self.client.get(url)
            self.assertEqual(response.status_code, 200, "No se recibio status "
                             "200 al realizar el render del detalle campana "
                             "en estado activo. Vista: {0}. URL: {1}"
                             "".format(vista, url))

        self.campana.estado = Campana.ESTADO_BORRADA
        self.campana.save()

        for url in VISTAS:
            url = reverse(vista, args=args)
            response = self.client.get(url)
            self.assertEqual(response.status_code, 400, "No se recibio status "
                             "400 al realizar el render del detalle campana "
                             "cuando la campana esta BORRADA. "
                             "Vista: {0}. URL: {1}"
                             "".format(vista, url))


class CampanaDetalleOpcionesTest(FTSenderBaseTest):
    """Testea que las vistas usadas para el detalle de opciones de la campaña
    sean accedidas con el estado correcto.
    """

    def setUp(self):
        self.user = User.objects.create_user('user', 'user@e.com', 'user')
        self.assertTrue(self.client.login(username='user', password='user'))
        self.campana = self.crear_campana()
        self.campana.activar()

        self.crea_calificaciones(self.campana)
        self.crea_todas_las_opcion_posibles(self.campana)
        self.crea_todas_las_actuaciones(self.campana)

    def test_detalle_opciones_campana(self):
        VISTAS = [
            ('detalle_estado_opciones', [self.campana.id])
        ]

        for vista, args in VISTAS:
            url = reverse(vista, args=args)
            response = self.client.get(url)
            self.assertEqual(response.status_code, 200, "No se recibio status "
                             "200 al realizar el render del detalle de estado "
                             " de la campana activa. Vista: {0}. URL: {1}"
                             "".format(vista, url))

        self.campana.estado = Campana.ESTADO_PAUSADA
        self.campana.save()

        for url in VISTAS:
            url = reverse(vista, args=args)
            response = self.client.get(url)
            self.assertEqual(response.status_code, 400, "No se recibio status "
                             "400 al realizar el render del detalle de estado "
                             "de la campana pausada. Vista: {0}. URL: {1}"
                             "".format(vista, url))


class CampanaEliminaTest(FTSenderBaseTest):
    """
    Testea la vista de eliminación de Templates. Que se visualice si el mismo
    se encuentra en el estado indicado.
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

    def test_eliminacion_campana(self):
        VISTAS = [
            ('campana_elimina', [self.campana.id]),
        ]

        for vista, args in VISTAS:
            url = reverse(vista, args=args)
            response = self.client.get(url)
            self.assertEqual(response.status_code, 200, "No se recibio status "
                             "200 al realizar el render inicial de la campana "
                             "definida para eliminar. Vista: {0}. URL: {1}"
                             "".format(vista, url))

        self.campana.estado = Campana.ESTADO_BORRADA
        self.campana.save()

        for url in VISTAS:
            url = reverse(vista, args=args)
            response = self.client.get(url)
            self.assertEqual(response.status_code, 400, "No se recibio status "
                             "400 al realizar el render de la campana "
                             "para eliminar cuando la campana ya esta en  "
                             "estado ESTADO_BORRADA."
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

    def test_creacion_template(self):

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
                             "200 al realizar el render inicial del template "
                             "en definicion. Vista: {0}. URL: {1}"
                             "".format(vista, url))

        self.campana.activar_template()

        for url in VISTAS:
            url = reverse(vista, args=args)
            response = self.client.get(url)
            self.assertEqual(response.status_code, 400, "No se recibio status "
                             "400 al realizar el render inicial del template "
                             "cuando el template ya NO ESTA en definicion. "
                             "Vista: {0}. URL: {1}"
                             "".format(vista, url))

    def test_detalle_template(self):
        VISTAS = [
            ('detalle_template', [self.campana.id]),
        ]

        for vista, args in VISTAS:
            url = reverse(vista, args=args)
            response = self.client.get(url)
            self.assertEqual(response.status_code, 400, "No se recibio status "
                             "400 al realizar el render del detalle template "
                             "cuando el template ya esta en definicion. "
                             "Vista: {0}. URL: {1}"
                             "".format(vista, url))

        self.campana.activar_template()

        for url in VISTAS:
            url = reverse(vista, args=args)
            response = self.client.get(url)
            self.assertEqual(response.status_code, 200, "No se recibio status "
                             "200 al realizar el render del detalle template "
                             "en estado activo. Vista: {0}. URL: {1}"
                             "".format(vista, url))

        self.campana.estado = Campana.ESTADO_TEMPLATE_BORRADO
        self.campana.save()

        for url in VISTAS:
            url = reverse(vista, args=args)
            response = self.client.get(url)
            self.assertEqual(response.status_code, 400, "No se recibio status "
                             "400 al realizar el render del detalle template "
                             "cuando el template ya NO ESTA en activo. "
                             "Vista: {0}. URL: {1}"
                             "".format(vista, url))


class TemplateDeCampanaEliminaTest(FTSenderBaseTest):
    """
    Testea la vista de eliminación de Templates. Que se visualice si el mismo
    se encuentra en el estado indicado.
    """
    def setUp(self):
        self.user = User.objects.create_user('user', 'user@e.com', 'user')
        self.assertTrue(self.client.login(username='user', password='user'))
        self.campana = self.crear_campana()
        self.campana.estado = Campana.ESTADO_TEMPLATE_ACTIVO
        self.campana.es_template = True
        self.campana.save()

        self.crea_calificaciones(self.campana)
        self.crea_todas_las_opcion_posibles(self.campana)
        self.crea_todas_las_actuaciones(self.campana)

    def test_eliminacion_template(self):
        VISTAS = [
            ('template_elimina', [self.campana.id]),
        ]

        for vista, args in VISTAS:
            url = reverse(vista, args=args)
            response = self.client.get(url)
            self.assertEqual(response.status_code, 200, "No se recibio status "
                             "200 al realizar el render inicial del template "
                             "definido para eliminar. Vista: {0}. URL: {1}"
                             "".format(vista, url))

        self.campana.estado = Campana.ESTADO_TEMPLATE_BORRADO
        self.campana.save()

        for url in VISTAS:
            url = reverse(vista, args=args)
            response = self.client.get(url)
            self.assertEqual(response.status_code, 400, "No se recibio status "
                             "400 al realizar el render inicial del template "
                             "para eliminar cuando el template ya esta en  "
                             "estado ESTADO_TEMPLATE_BORRADO."
                             "Vista: {0}. URL: {1}"
                             "".format(vista, url))

    def test_crea_campana_de_template(self):
        VISTAS = [
            ('crea_campana_template', [self.campana.id]),
        ]

        for vista, args in VISTAS:
            url = reverse(vista, args=args)
            response = self.client.get(url)
            self.assertEqual(response.status_code, 302, "No se recibio el "
                             "estado correcto del template para crear la "
                             "campaña a partir de este. Vista: {0}. URL: {1}"
                             "".format(vista, url))

        self.campana.estado = Campana.ESTADO_TEMPLATE_BORRADO
        self.campana.save()

        for url in VISTAS:
            url = reverse(vista, args=args)
            response = self.client.get(url)
            self.assertEqual(response.status_code, 400, "No se recibio status "
                             "400 al intentar la creación de una campaña a "
                             "partir de un template en estado incorrecto. "
                             "Vista: {0}. URL: {1}"
                             "".format(vista, url))


class ReciclarCampanaTest(FTSenderBaseTest):
    """Testea que las vistas usadas para reciclar una campanas NO puedan
    ser utilizadas si lamisma no esta en estado depurada.
    Y testea que las vistas usadas en el proceso de redefinición delreciclado
    no puedan ser utilizadas una vez terminado el proceso de reciclado.
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

    def test_reciclado_campana(self):

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
    def setUp(self):
        self.user = User.objects.create_user('user', 'user@e.com', 'user')
        self.assertTrue(self.client.login(username='user', password='user'))

        self.base_datos_contacto = self.crear_base_datos_contacto()
        self.base_datos_contacto.archivo_importacion = File(
            open(self.get_test_resource("planilla-ejemplo-1.csv"), 'r'))
        self.base_datos_contacto.save()

    def test_creacion_base_datos_contacto(self):

        VISTAS = [
            ('define_base_datos_contacto', [self.base_datos_contacto.id]),
        ]

        for vista, args in VISTAS:
            url = reverse(vista, args=args)
            response = self.client.get(url)
            self.assertEqual(response.status_code, 200, "No se recibio status "
                             "200 al realizar el render inicial de la BD "
                             "en definicion. Vista: {0}. URL: {1}"
                             "".format(vista, url))

        self.base_datos_contacto.define()

        for url in VISTAS:
            url = reverse(vista, args=args)
            response = self.client.get(url)
            self.assertEqual(response.status_code, 400, "No se recibio status "
                             "400 al realizar el render inicial de la BD "
                             "cuando la BD ya NO ESTA en definicion. "
                             "Vista: {0}. URL: {1}"
                             "".format(vista, url))

    def test_depuracion_base_datos_contacto(self):
        VISTAS = [
            ('depurar_base_datos_contacto', [self.base_datos_contacto.id]),
        ]

        self.base_datos_contacto.define()

        for vista, args in VISTAS:
            url = reverse(vista, args=args)
            response = self.client.get(url)
            self.assertEqual(response.status_code, 200, "No se recibio status "
                             "200 al realizar el render inicial de la "
                             "depuración de la BD ya definida. "
                             "Vista: {0}. URL: {1}"
                             "".format(vista, url))

        self.base_datos_contacto.estado = BaseDatosContacto.ESTADO_DEPURADA
        self.base_datos_contacto.save()

        for url in VISTAS:
            url = reverse(vista, args=args)
            response = self.client.get(url)
            self.assertEqual(response.status_code, 400, "No se recibio status "
                             "400 al realizar el render inicial de la "
                             "depuración de la BD en estado depurada."
                             "Vista: {0}. URL: {1}"
                             "".format(vista, url))
        