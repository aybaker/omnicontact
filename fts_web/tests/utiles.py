# -*- coding: utf-8 -*-

"""Metodos utilitarios para ser reutilizados en los distintos
módulos de tests.

ATENCION: aqui NO estan los tests del paquete 'fts_web.utiles',
sino que estan los metodos utilitarios para facilitar el
desarrollo de los tests.
"""

from __future__ import unicode_literals

import datetime
import logging
import os
import random
import uuid

from django.conf import settings
from django.test import TestCase
from django.test.runner import DiscoverRunner
from django.test.testcases import LiveServerTestCase, TransactionTestCase
from fts_daemon.models import EventoDeContacto
from fts_web.models import GrupoAtencion, Calificacion, AgenteGrupoAtencion, \
    Contacto, BaseDatosContacto, Campana, Opcion, Actuacion


EV_FINALIZADOR = EventoDeContacto.objects.\
    get_eventos_finalizadores()[0]


class FTSenderDiscoverRunner(DiscoverRunner):
    """
    Test runner para FTSender
    """

    def __init__(self, *args, **kwargs):
        settings.FTS_TESTING_MODE = True

        for db in settings.DATABASES.values():
            if db.get('CONN_MAX_AGE', 0) != 0:
                print "Patcheando CONN_MAX_AGE: {0} -> 0".format(
                    db['CONN_MAX_AGE'])
                db['CONN_MAX_AGE'] = 0

        for key in os.environ.keys():
            if key.find("proxy") > -1:
                del os.environ[key]

        # Settings para Celery
        settings.BROKER_BACKEND = 'memory'
        settings.CELERY_ALWAYS_EAGER = True
        settings.CELERY_EAGER_PROPAGATES_EXCEPTIONS = True

        super(FTSenderDiscoverRunner, self).__init__(*args, **kwargs)

        def handleError(self, record):
            raise

        logging.Handler.handleError = handleError


def _get_webdriver():
    # Siempre usamos Firefox, por ahora
    from selenium.webdriver.firefox.webdriver import \
        WebDriver  # @UnresolvedImport
    return WebDriver()

    #chromedriver_bin = None
    #try:
    #    chromedriver_bin = subprocess.check_output(
    #        ["which", "chromedriver"],
    #        stderr=subprocess.STDOUT)
    #except subprocess.CalledProcessError:
    #    for an_executable in settings.SELENIUM_WEBDRIVER_BIN:
    #        if os.path.exists(an_executable):
    #            chromedriver_bin = an_executable
    #            break
    #if chromedriver_bin is not None:
    #    from selenium.webdriver.chrome.webdriver import WebDriver
    #        as ChromeWebDriver
    #    return ChromeWebDriver(executable_path=chromedriver_bin)
    #else:
    #    from selenium.webdriver.firefox.webdriver import WebDriver
    #        as FirefoxWebDriver
    #    return FirefoxWebDriver()


class FTSenderSeleniumBaseTest(LiveServerTestCase):

    MARCA_RENDER_OK = "<!-- SELENIUM-REDER-OK-True -->"

    def assertTrueSelenium(self, *args, **kwargs):
        """Ejecuta assertTrue(), y si falla, el valor del setting
        'FTS_STOP_ON_SELENIUM_ASSERT_ERROR' es evaluado.
        - Si 'FTS_STOP_ON_SELENIUM_ASSERT_ERROR' es True, el test es
            pausado, para que se pueda ver el error en la pantalla
        - Si 'FTS_STOP_ON_SELENIUM_ASSERT_ERROR' es False, el test continua

        Una forma de usarlo es la siguiente:

        @override_settings(FTS_STOP_ON_SELENIUM_ASSERT_ERROR=True, DEBUG=True)
        def un_metodo(self):
            pass
        """
        try:
            self.assertTrue(*args, **kwargs)
        except AssertionError:
            if settings.FTS_STOP_ON_SELENIUM_ASSERT_ERROR:
                import pdb
                pdb.set_trace()
            raise

    def render_y_chequear(self, url):
        """Renderiza `url` con Selenium, espera que finalice el
        cargado de la página, y chequea que exista en el
        HTML la `MARCA_RENDER_OK`.
        """
        self.selenium.get('%s%s' % (self.live_server_url, url))
        self._wait_until_render_done()
        self.assertTrueSelenium(self.selenium.page_source.find(
            FTSenderSeleniumBaseTest.MARCA_RENDER_OK) >= 0)

    @classmethod
    def setUpClass(cls):
        cls.selenium = _get_webdriver()
        super(FTSenderSeleniumBaseTest, cls).setUpClass()

    @classmethod
    def tearDownClass(cls):
        cls.selenium.quit()
        super(FTSenderSeleniumBaseTest, cls).tearDownClass()

    def _wait_until_render_done(self):
        """
        Wait until the browser finished rendering the HTML.
        To be used after clics, submits. etc.
        """
        from selenium.webdriver.support.wait import \
            WebDriverWait  # @UnresolvedImport
        WebDriverWait(self.selenium, 5).until(
            lambda driver: driver.find_element_by_tag_name('body'))


def ru():
    """Devuelve random UUID"""
    return str(uuid.uuid4())


def rtel():
    """Devuelve nro telefonico aleatorio"""
    return random.randint(1140000000, 1149999999)


class FTSenderTestUtilsMixin(object):

    def get_test_resource(self, resource):
        """Devuelve el path completo a archivo del directorio test/
        o resources/
        """
        tmp = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        resource1 = os.path.join(tmp, "test", resource)
        resource2 = os.path.join(tmp, "fts_tests", "resources", resource)
        if os.path.exists(resource1):
            return resource1
        elif os.path.exists(resource2):
            return resource2

        self.fail("Resource {0} no existe en ningulo "
            "de los directorios buscados".format(resource))

    def read_test_resource(self, resource):
        """Devuelve el contenido de un archivo del directorio test/"""
        tmp = self.get_test_resource(resource)
        with open(tmp, 'r') as f:
            return f.read()

    def crear_grupo_atencion(self):
        """Crea un grupo de atencion"""
        return GrupoAtencion.objects.create(
            nombre="grupo-at-" + ru(), timeout=18)

    def crea_calificaciones(self, campana):
        """Crea conjunto de calificaciones para capana"""
        Calificacion.objects.create(
            nombre="Excelente",
            campana=campana)
        Calificacion.objects.create(
            nombre="Muy bueno",
            campana=campana)
        Calificacion.objects.create(
            nombre="Bueno",
            campana=campana)
        Calificacion.objects.create(
            nombre="Malo",
            campana=campana)
        Calificacion.objects.create(
            nombre="Muy malo",
            campana=campana)

    def crear_agente(self, grupo_atencion):
        """Crea un agente"""
        return AgenteGrupoAtencion.objects.create(
            numero_interno=str(random.randint(1000000, 5000000)),
            grupo_atencion=grupo_atencion)

    def crear_contacto(self, bd_contacto, nro_telefonico=None):
        """Crea un contacto asociado a la base de datos de
        contactos especificada.
        - bd_contacto: base de datos de contactos a la que
            pertenece el contacto
        - nro_telefonico: nro telefonico del contacto. Si no se epscifica
            o es None, se genera un numero aleatorio
        """
        nro_telefonico = nro_telefonico or rtel()
        return Contacto.objects.create(telefono=nro_telefonico,
            datos="{}", bd_contacto=bd_contacto)

    def crear_base_datos_contacto(self, cant_contactos=None,
        numeros_telefonicos=None):
        """Crea base datos contacto
        - cant_contactos: cantidad de contactos a crear.
            Si no se especifica, se genera una cantidad
            aleatoria de contactos
        - numeros_telefonicos: lista con numeros de contactos a crear.
            Si se especifica, se ignora el valor `cant_contactos`
        """
        bd_contacto = BaseDatosContacto.objects.create(
            nombre="base-datos-contactos-" + ru())
        if numeros_telefonicos is not None:
            for nro_telefonico in numeros_telefonicos:
                self.crear_contacto(
                    bd_contacto, nro_telefonico=nro_telefonico)
            bd_contacto.cantidad_contactos = len(numeros_telefonicos)
            bd_contacto.save()
            return bd_contacto

        if cant_contactos is None:
            cant_contactos = random.randint(3, 7)
        for _ in range(0, cant_contactos):
            self.crear_contacto(bd_contacto)
        bd_contacto.cantidad_contactos = cant_contactos
        bd_contacto.save()

        return bd_contacto

    def crear_campana(self, fecha_inicio=None, fecha_fin=None,
        cant_contactos=None, bd_contactos=None, **kwargs):
        """Crea una campana en su estado inicial
        - cant_contactos: cant. de contactos a crear para la campaña
            Si es None, se generara un nro. aleatorio de contactos
        - bd_contactos: base de datos de contactos a usar. Si es
            None, se generara una nueva. Si se especifica, entonces
            el valor de `cant_contactos` es ignorado
        - fecha_inicio: fecha de inicio de la campaña. Si es None
            utiliza una por default.
        - fecha_fin: fecha de fin de la campaña. Si es None
            utiliza una por default.
        """

        cantidad_canales = kwargs.get('cantidad_canales', 2)
        cantidad_intentos = kwargs.get('cantidad_intentos', 2)

        if bd_contactos:
            assert bd_contactos.get_cantidad_contactos() > cantidad_canales, \
                "La cant. de contactos en BD debe ser mayor a cant. canales"
        else:
            if cant_contactos is not None:
                assert cant_contactos > cantidad_canales, \
                    "La cant. de contactos en BD debe ser mayor a los canales"
            bd_contactos = self.crear_base_datos_contacto(
                cant_contactos=cant_contactos)

        if not fecha_inicio or not fecha_fin:
            fecha_inicio = datetime.date.today()
            fecha_fin = fecha_inicio + datetime.timedelta(days=10)

        c = Campana(
            nombre="campaña-" + ru(),
            cantidad_canales=cantidad_canales,
            cantidad_intentos=cantidad_intentos,
            segundos_ring=5,
            fecha_inicio=fecha_inicio,
            fecha_fin=fecha_fin,
            bd_contacto=bd_contactos,
            audio_original="test/audio/original.wav",
            audio_asterisk="test/audio/for-asterisk.wav",
        )
        c.save()

        c.nombre = "Campaña de PRUEBA - {0}".format(c.id)
        c.save()

        return c

    def crear_campana_sin_audio(self, fecha_inicio=None, fecha_fin=None,
        cant_contactos=None, bd_contactos=None):
        """Crea una campana en su estado inicial
        - cant_contactos: cant. de contactos a crear para la campaña
            Si es None, se generara un nro. aleatorio de contactos
        - bd_contactos: base de datos de contactos a usar. Si es
            None, se generara una nueva. Si se especifica, entonces
            el valor de `cant_contactos` es ignorado
        - fecha_inicio: fecha de inicio de la campaña. Si es None
            utiliza una por default.
        - fecha_fin: fecha de fin de la campaña. Si es None
            utiliza una por default.
        """

        bd_contactos = bd_contactos or self.crear_base_datos_contacto(
            cant_contactos=cant_contactos)

        if not fecha_inicio or not fecha_fin:
            fecha_inicio = datetime.date.today()
            fecha_fin = fecha_inicio + datetime.timedelta(days=10)

        c = Campana(
            nombre="campaña-" + ru(),
            cantidad_canales=2,
            cantidad_intentos=2,
            segundos_ring=5,
            fecha_inicio=fecha_inicio,
            fecha_fin=fecha_fin,
            bd_contacto=bd_contactos,
        )
        c.save()
        return c

    def crear_campana_activa(self, cant_contactos=None, bd_contactos=None,
        *args, **kwargs):
        """Crea campañas y la pasa a ESTADO_ACTIVA."""

        c = self.crear_campana(cant_contactos=cant_contactos,
            bd_contactos=bd_contactos, *args, **kwargs)
        c.activar()
        return c

    def crear_campana_finalizada(self, *args, **kwargs):
        """Crea campañas y la pasa a ESTADO_ACTIVA.
        """
        c = self.crear_campana(*args, **kwargs)
        c.activar()
        c.finalizar()
        return c

    def crea_campana_opcion(self, digito, campana, accion=None,
        grupo_atencion=None, calificacion=None):
        """
        Crea un opbjeto Opccion relacionado a una
        Campana, la cuál se tiene que tomar como
        parámetro.
        """
        if not accion:
            accion = Opcion.REPETIR

        opcion = Opcion(
            digito=digito,
            accion=Opcion.REPETIR,
            grupo_atencion=grupo_atencion,
            calificacion=calificacion,
            campana=campana,
        )
        opcion.save()
        return opcion

    def crea_todas_las_opcion_posibles(self, campana):
        """
        Crea todas los tipos posibles de Opciones
        """
        #
        # Atencion! Esto *NO* está terminado...
        # A medida que se implementen los distintos tipos de
        #  acciones, hará falta ir actualizando este método
        #

        Opcion(
            digito=0,
            accion=Opcion.REPETIR,
            campana=campana,
        ).save()

        #Por el momento no va VOICEMAIL.
        # Opcion(
        #     digito=1,
        #     accion=Opcion.VOICEMAIL,
        #     campana=campana,
        # ).save()

        try:
            ga = GrupoAtencion.objects.all()[0]
        except IndexError:
            ga = self.crear_grupo_atencion()

        Opcion(
            digito=2,
            accion=Opcion.DERIVAR_GRUPO_ATENCION,
            campana=campana,
            grupo_atencion=ga,
        ).save()

        digito = 3
        for calif in campana.calificaciones.all():
            if digito > 9:
                break
            Opcion(
                digito=digito,
                accion=Opcion.CALIFICAR,
                campana=campana,
                calificacion=calif,
            ).save()
            digito += 1

    def crea_campana_actuacion(self, dia_semanal,
        hora_desde, hora_hasta, campana):
        """
        Crea un opbjeto Actuacion relacionado a una
        Campana, la cuál se tiene que tomar como
        parámetro.
        """

        actuacion = Actuacion(
            dia_semanal=dia_semanal,
            hora_desde=hora_desde,
            hora_hasta=hora_hasta,
            campana=campana,
        )
        actuacion.save()
        return actuacion

    def crea_todas_las_actuaciones(self, campana):
        """
        Crea un opbjeto Actuacion para c/dia de la semana,
        desde las 00:00 hasta las 23:59
        """
        for weekday in range(0, 7):
            self.crea_campana_actuacion(weekday,
                datetime.time(0, 00), datetime.time(23, 59), campana)

    def registra_evento_de_intento(self, campana_id, contacto_id, intento):
        """Genera evento asociado a intento de contactacion"""
        EventoDeContacto.objects.inicia_intento(campana_id, contacto_id,
            intento)

    def registra_evento_de_finalizacion(self, campana_id, contacto_id,
        intento):
        """Genera evento asociado a finalizacion de contacto"""
        EventoDeContacto.objects.create(campana_id=campana_id,
            contacto_id=contacto_id, evento=EV_FINALIZADOR,
            dato=intento)

    def _crea_campana_emula_procesamiento(self, evento=None,
        cantidad_eventos=None, finaliza=True):

        cant_contactos = 100
        numeros_telefonicos = [int(random.random() * 10000000000)\
            for _ in range(cant_contactos)]

        base_datos_contactos = self.crear_base_datos_contacto(
            cant_contactos=cant_contactos,
            numeros_telefonicos=numeros_telefonicos)

        campana = self.crear_campana(bd_contactos=base_datos_contactos,
            cantidad_intentos=3)
        campana.activar()

        self.crea_todas_las_actuaciones(campana)
        self.crea_calificaciones(campana)
        self.crea_todas_las_opcion_posibles(campana)

        #Progrmaa la campaña.
        EventoDeContacto.objects_gestion_llamadas.programar_campana(
            campana.pk)

        numero_interno = 1
        #for numero_interno in range(1, campana.cantidad_intentos):
        #Intentos.
        EventoDeContacto.objects_simulacion.simular_realizacion_de_intentos(
            campana.pk, numero_interno, probabilidad=1.1)

        if evento:
            contactos = base_datos_contactos.contactos.all()[
                0:cantidad_eventos]
            for contacto in contactos:
                EventoDeContacto.objects.create(
                    campana_id=campana.pk,
                    contacto_id=contacto.pk,
                    evento=evento,
                    dato=numero_interno,
                )


        #Opciones
        EventoDeContacto.objects_simulacion.simular_evento(campana.pk,
            numero_interno, EventoDeContacto.EVENTO_ASTERISK_OPCION_0,
            probabilidad=0.03)
        EventoDeContacto.objects_simulacion.simular_evento(campana.pk,
            numero_interno, EventoDeContacto.EVENTO_ASTERISK_OPCION_1,
            probabilidad=0.02)
        EventoDeContacto.objects_simulacion.simular_evento(campana.pk,
            numero_interno, EventoDeContacto.EVENTO_ASTERISK_OPCION_2,
            probabilidad=0.01)
        EventoDeContacto.objects_simulacion.simular_evento(campana.pk,
            numero_interno, EventoDeContacto.EVENTO_ASTERISK_OPCION_3,
            probabilidad=0.05)
        EventoDeContacto.objects_simulacion.simular_evento(campana.pk,
            numero_interno, EventoDeContacto.EVENTO_ASTERISK_OPCION_4,
            probabilidad=0.25)
        # EventoDeContacto.objects_simulacion.simular_evento(campana.pk,
        #     numero_interno, EventoDeContacto.EVENTO_ASTERISK_OPCION_5,
        #     probabilidad=0.15)
        # EventoDeContacto.objects_simulacion.simular_evento(campana.pk,
        #     numero_interno, EventoDeContacto.EVENTO_ASTERISK_OPCION_6,
        #     probabilidad=0.05)
        # EventoDeContacto.objects_simulacion.simular_evento(campana.pk,
        #     numero_interno, EventoDeContacto.EVENTO_ASTERISK_OPCION_7,
        #     probabilidad=0.05)

        #Opciones inválidas para esta campaña.
        EventoDeContacto.objects_simulacion.simular_evento(campana.pk,
            numero_interno, EventoDeContacto.EVENTO_ASTERISK_OPCION_8,
            probabilidad=0.02)
        # EventoDeContacto.objects_simulacion.simular_evento(campana.pk,
        #     numero_interno, EventoDeContacto.EVENTO_ASTERISK_OPCION_9,
        #     probabilidad=0.02)

        #Finaliza algunos.
        EV_FINALIZADOR = EventoDeContacto.objects.\
        get_eventos_finalizadores()[0]
        EventoDeContacto.objects_simulacion.simular_evento(campana.pk,
            numero_interno, evento=EV_FINALIZADOR, probabilidad=0.15)

        if finaliza:
            campana.finalizar()
        return campana

class FTSenderBaseTransactionTestCase(TransactionTestCase,
    FTSenderTestUtilsMixin):
    """Clase base para tests"""


class FTSenderBaseTest(TestCase, FTSenderTestUtilsMixin):
    """Clase base para tests"""


def default_db_is_postgresql():
    """Devuelve si la DB por default es PostgreSql"""
    return settings.DATABASES['default']['ENGINE'] == \
        'django.db.backends.postgresql_psycopg2'
