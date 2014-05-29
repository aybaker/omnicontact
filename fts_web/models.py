# -*- coding: utf-8 -*-

"""
Modelos de la aplicación
"""

from __future__ import unicode_literals

from collections import defaultdict
import csv
import datetime
import logging
import os
import math

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models

from django.db.models import Sum, Q
from fts_web.utiles import crear_archivo_en_media_root, upload_to
import pygal
from pygal.style import Style


logger = logging.getLogger(__name__)


#==============================================================================
# Grupos de Atención
#==============================================================================

class GrupoAtencionManager(models.Manager):
    """Manager para GrupoAtencion"""

    def obtener_todos_para_generar_config(self):
        """Devuelve g.a. que deben ser tenidas en cuenta
        al generar el configuracoin de queues.
        """
        return self.all()


class GrupoAtencion(models.Model):
    """
    Representa un Grupo de Atencion, o sea, un conjunto de agentes
    a donde se puede derivar una llamada.

    Se sobreescribe el método `delete()` para implementar
    un borrado lógico.
    """

    objects = GrupoAtencionManager()

    RINGALL, RRMEMORY = range(0, 2)
    RING_STRATEGY_CHOICES = (
        (RINGALL, 'RINGALL'),
        (RRMEMORY, 'RRMEMORY'),
    )

    RING_STRATEGY_PARA_ASTERISK = dict([
        (RINGALL, 'ringall'),
        (RRMEMORY, 'rrmemory'),
    ])
    """Texto a usar en configuracion de Asterisk"""

    nombre = models.CharField(
        max_length=128,
    )
    timeout = models.PositiveIntegerField()
    ring_strategy = models.PositiveIntegerField(
        choices=RING_STRATEGY_CHOICES,
        default=RINGALL,
    )
    #    active = models.BooleanField(
    #        default=True,
    #        editable=False,
    #    )

    def __unicode__(self):
        return self.nombre
        #    if self.active:
        #        return self.nombre
        #    return '(ELiminado) {0}'.format(self.nombre)

    #    def delete(self, *args, **kwargs):
    #        if self.active:
    #            self.active = False
    #            self.save()

    def get_cantidad_agentes(self):
        return self.agentes.all().count()

    def get_nombre_para_asterisk(self):
        """Devuelve un texto para ser usado en Asterisk,
        para identificar este grupo de atencion.
        """
        assert self.id
        return 'fts_grupo_atencion_{0}'.format(self.id)

    def get_ring_strategy_para_asterisk(self):
        """Devuelve un texto para ser usado en Asterisk,
        para identificar la ring_strategy seleccionada.
        """
        return GrupoAtencion.RING_STRATEGY_PARA_ASTERISK[self.ring_strategy]


class AgenteGrupoAtencion(models.Model):
    numero_interno = models.CharField(
        max_length=32,
    )
    grupo_atencion = models.ForeignKey(
        'GrupoAtencion',
        related_name='agentes'
    )
    #    active = models.BooleanField(
    #        default=True,
    #        editable=False,
    #    )

    def __unicode__(self):
        return '{0} >> {1}'.format(
            self.grupo_atencion, self.numero_interno)
        #    if self.active:
        #        return '{0} >> {1}'.format(
        #            self.grupo_atencion, self.numero_interno)
        #    return '(ELiminado) {0} >> {1}'.format(
        #            self.grupo_atencion, self.numero_interno)

    #    def delete(self, *args, **kwargs):
    #        if self.active:
    #            self.active = False
    #            self.save()


#==============================================================================
# Base Datos Contactos
#==============================================================================

class BaseDatosContactoManager(models.Manager):
    """Manager para BaseDatosContacto"""

    def obtener_definidas(self):
        """
        Este método filtra lo objetos BaseDatosContacto que
        esté definidos.
        """
        return self.filter(sin_definir=False)


upload_to_archivos_importacion = upload_to("archivos_importacion", 95)


class BaseDatosContacto(models.Model):
    objects = BaseDatosContactoManager()

    nombre = models.CharField(
        max_length=128,
    )
    fecha_alta = models.DateTimeField(
        auto_now_add=True,
    )
    columnas = models.CharField(
        max_length=256,
        blank=True, null=True,
    )
    archivo_importacion = models.FileField(
        upload_to=upload_to_archivos_importacion,
        max_length=100,
    )
    nombre_archivo_importacion = models.CharField(
        max_length=256,
    )
    sin_definir = models.BooleanField(
        default=True,
    )
    columna_datos = models.PositiveIntegerField(
        blank=True, null=True,
    )
    cantidad_contactos = models.PositiveIntegerField(
        default=0
    )

    #    active = models.BooleanField(
    #        default=True,
    #        editable=False,
    #    )

    def __unicode__(self):
        return self.nombre
        #    if self.active:
        #        return self.nombre
        #    return '(ELiminado) {0}'.format(self.nombre)

    def importa_contactos(self, parser_archivo):
        """
        Este metodo se encarga de realizar la importación de los
        teléfonos del archivo guardado. Por cada teléfono del
        archivo crea un objeto Contacto con el teléfono y lo
        relaciona la instancia actual de BaseDatosContacto.
        Parametros:
        - parser_archivo: Instacia del parser adecuado según el
        tipo de archivo subido.

        """

        lista_telefonos = parser_archivo.read_file(self.columna_datos,
            self.archivo_importacion.file)
        if lista_telefonos:
            for telefono in lista_telefonos:
                Contacto.objects.create(
                    telefono=telefono,
                    bd_contacto=self,
                )
            self.cantidad_contactos = len(lista_telefonos)
            return True
        return False

    def define(self):
        """
        Este método se encara de llevar a cabo la definición del
        objeto BaseDatosContacto. Establece el atributo sin_definir
        en False haciedo que quede disponible el objeto.
        """

        logger.info("Seteando base datos contacto %s como definida", self.id)
        self.sin_definir = False
        self.save()

    def get_cantidad_contactos(self):
        """
        Devuelve la cantidad de contactos de la BaseDatosContacto.
        """

        return self.cantidad_contactos


class Contacto(models.Model):
    telefono = models.CharField(
        max_length=64,
    )
    datos = models.TextField(
        blank=True, null=True,
    )
    bd_contacto = models.ForeignKey(
        'BaseDatosContacto',
        related_name='contactos'
    )

    def __unicode__(self):
        return '{0} >> {1}'.format(
            self.bd_contacto, self.telefono)


#==============================================================================
# Campaña
#==============================================================================

class CampanaManager(models.Manager):
    """Manager para Campanas"""

    def obtener_activas(self):
        """Devuelve campañas en estado activas.
        Puede suceder que este metodo devuelva campañas en estado activas,
        pero que en realidad deberian estar en estado FINALIZADAS porque,
        por ejemplo, la fecha actual es posterior a "fecha de fin", todavía
        no se actualizó el estado de dichas campañas en la BD.
        """
        return self.filter(estado=Campana.ESTADO_ACTIVA)

    def obtener_pausadas(self):
        """
        Devuelve campañas en estado pausadas.
        """
        return self.filter(estado=Campana.ESTADO_PAUSADA)

    def obtener_finalizadas(self):
        """Devuelve campañas en estado finalizadas."""
        return self.filter(estado=Campana.ESTADO_FINALIZADA)

    def obtener_todas_para_generar_dialplan(self):
        """Devuelve campañas que deben ser tenidas en cuenta
        al generar el dialplan.
        """
        # TODO: renombrar a `obtener_todas_para_generar_config()`
        # TODO: si estan finalizadas y vencidas con más de 1 día,
        #  podemos estar tranquilos de que no habra llamadas
        #  para esas campañas, y podriamos ignorarlas
        return self.filter(estado__in=[Campana.ESTADO_ACTIVA,
            Campana.ESTADO_PAUSADA, Campana.ESTADO_FINALIZADA])

    def obtener_ejecucion(self):
        """
        Devuelve las campanas que tengan actuación en el
        momento de realizar la consulta.
        """
        #Fecha y Hora local.
        hoy_ahora = datetime.datetime.today()
        dia_semanal = hoy_ahora.weekday()
        fecha_actual = hoy_ahora.date()
        hora_actual = hoy_ahora.time()

        campanas_hoy = self.obtener_activas().filter(
            fecha_inicio__lte=fecha_actual,
            fecha_fin__gte=fecha_actual)

        campanas_ejecucion = campanas_hoy.filter(
            actuaciones__dia_semanal=dia_semanal,
            actuaciones__hora_desde__lte=hora_actual,
            actuaciones__hora_hasta__gte=hora_actual)

        return campanas_ejecucion

    def verifica_estado_activa(self, campana_id):
        """Devuelve booleano indicando si el estado de la campaña
        es 'ACTIVA'
        :param campana_id: Id de la campaña
        :type pk: int
        :returns: bool -- si la campaña esta activa o no
        """
        return self.filter(pk=campana_id,
            estado=Campana.ESTADO_ACTIVA).exists()

    def finalizar_vencidas(self):
        """Busca campañas vencidas, y las finaliza"""
        # Aca necesitamos *localtime*. Usamos `now_ref` como fecha de
        # referencia para todos los calculos

        # FIXME: aunque necesitamos utilizar la hora local, esto hace
        # muy complicado crear un algoritmo respetable que funcione en
        # escenarios de cambios horarios!
        # El problema es que las actuaciones son basadas en hora (sin TZ),
        # por lo tanto, tecnicamente, si justo despues de las 23:59:59.999
        # se pasa a las 23:00:00.000 del mismo día, entonces algunas
        # Actuaciones podrían ser validas 2 veces!

        now_ref = datetime.datetime.now()

        estados = [Campana.ESTADO_ACTIVA, Campana.ESTADO_PAUSADA]

        #
        # Primero finalizamos viejas, de ayer o anteriores
        #

        queryset = self.filter(
            fecha_fin__lt=now_ref.date(),
            estado__in=estados
        )

        # A las viejas, las finalizamos de una
        for campana in queryset:
            logger.info("finalizar_vencidas(): finalizando campana %s. "
                "Su 'fecha_fin' es anterior a la fecha actual", campana.id)
            campana.finalizar()

        #
        # Si hay alguna q' finalice hoy, hay q' revisar las actuaciones
        #

        queryset = self.filter(
            fecha_fin=now_ref.date(),
            estado__in=estados
        ).select_related('actuaciones')

        for campana in queryset:
            actuaciones_para_hoy = [actuacion
                for actuacion in campana.actuaciones.all()
                if actuacion.dia_concuerda(now_ref.date())]

            # Si no tiene actuaciones para hoy, la finalizamos!
            if not actuaciones_para_hoy:
                logger.info("finalizar_vencidas(): finalizando campana %s. "
                    "Su 'fecha_fin' es hoy, pero no posee Actuacion para hoy",
                    campana.id)
                campana.finalizar()
                continue

            # Si todas las actuaciones para hoy, tienen una
            # hora_fin menor a la actual, entonces podemos
            # finalizar la campaña
            son_anteriores = [act.es_anterior_a(now_ref.time())
                for act in actuaciones_para_hoy]
            if all(son_anteriores):
                # Todas las Actuaciones para hoy, poseen una
                # hora_desde / hora_hasta ANTERIOR a la actual
                # por lo tanto, podemos finalizar la campaña
                logger.info("finalizar_vencidas(): finalizando campana %s. "
                    "Su 'fecha_fin' es hoy, posee Actuacion pero todas "
                    "ya han finalizado", campana.id)
                campana.finalizar()
                continue

upload_to_audios_asterisk = upload_to("audios_asterisk", 95)
upload_to_audios_originales = upload_to("audios_reproduccion", 95)


class Campana(models.Model):
    """Una campaña del call center"""

    objects = CampanaManager()

    ESTILO_VERDE_ROJO_NARANJA = Style(
        background='transparent',
        plot_background='transparent',
        foreground='#555',
        foreground_light='#FFF',
        foreground_dark='#FFF',
        opacity='.8',
        opacity_hover='1',
        transition='400ms ease-in',
        colors=('#5cb85c', '#d9534f', '#f0ad4e')
    )

    ESTILO_MULTICOLOR = Style(
        background='transparent',
        plot_background='transparent',
        foreground='#555',
        foreground_light='#FFF',
        foreground_dark='#FFF',
        opacity='.8',
        opacity_hover='1',
        transition='400ms ease-in',
        colors=('#428bca', '#5cb85c', '#5bc0de', '#f0ad4e', '#d9534f',
            '#a95cb8', '#5cb8b5', '#caca43', '#96ac43', '#ca43ca')
    )

    ESTADO_EN_DEFINICION = 1
    """La campaña esta siendo definida en el wizard"""

    ESTADO_ACTIVA = 2
    """La campaña esta activa, o sea, EN_CURSO o PROGRAMADA
    A nivel de modelos, solo queremos registrar si está ACTIVA, y no nos
    importa si esta EN_CURSO (o sea, si en este momento el daemon está
    generando llamadas asociadas a la campaña) o PROGRAMADA (si todavia no
    estamos en el rango de dias y horas en los que se deben generar
    las llamadas)
    """

    ESTADO_PAUSADA = 3
    """La capaña fue pausada"""

    ESTADO_FINALIZADA = 4
    """La campaña fue finalizada, automatica o manualmente"""

    ESTADOS = (
        (ESTADO_EN_DEFINICION, '(en definicion)'),
        (ESTADO_ACTIVA, 'Activa'),
        (ESTADO_PAUSADA, 'Pausada'),
        (ESTADO_FINALIZADA, 'Finalizada'),
    )

    nombre = models.CharField(
        max_length=128,
    )
    estado = models.PositiveIntegerField(
        choices=ESTADOS,
        default=ESTADO_EN_DEFINICION,
    )
    cantidad_canales = models.PositiveIntegerField()
    cantidad_intentos = models.PositiveIntegerField()
    segundos_ring = models.PositiveIntegerField()
    fecha_inicio = models.DateField()
    fecha_fin = models.DateField()
    audio_original = models.FileField(
        upload_to=upload_to_audios_originales,
        max_length=100,
        null=True, blank=True,
    )
    audio_asterisk = models.FileField(
        upload_to=upload_to_audios_asterisk,
        max_length=100,
        null=True, blank=True,
    )

    bd_contacto = models.ForeignKey(
        'BaseDatosContacto',
        related_name='campanas'
    )

    def activar(self):
        """Setea la campaña como ACTIVA, y genera los IntentoDeContacto
        asociados a esta campaña
        """
        logger.info("Seteando campana %s como ACTIVA", self.id)
        assert self.estado == Campana.ESTADO_EN_DEFINICION
        self.estado = Campana.ESTADO_ACTIVA
        self.save()

        # FIXME: este proceso puede ser costoso, deberia ser asincrono
        # TODO: log timing
        from fts_daemon.models import EventoDeContacto
        EventoDeContacto.objects_gestion_llamadas.programar_campana(
            self.id)

    def finalizar(self):
        """
        Setea la campaña como finalizada.
        """
        logger.info("Seteando campana %s como ESTADO_FINALIZADA", self.id)
        # TODO: esta bien generar error si el modo actual es ESTADO_FINALIZADA?
        assert self.estado in (Campana.ESTADO_ACTIVA, Campana.ESTADO_PAUSADA)
        self.estado = Campana.ESTADO_FINALIZADA
        self.save()

    def pausar(self):
        """Setea la campaña como ESTADO_PAUSADA"""
        logger.info("Seteando campana %s como ESTADO_PAUSADA", self.id)
        assert self.estado == Campana.ESTADO_ACTIVA
        self.estado = Campana.ESTADO_PAUSADA
        self.save()

    def despausar(self):
        """Setea la campaña como ESTADO_ACTIVA.
        """
        logger.info("Seteando campana %s como ESTADO_ACTIVA", self.id)
        assert self.estado == Campana.ESTADO_PAUSADA
        self.estado = Campana.ESTADO_ACTIVA
        self.save()

    def obtener_actuacion_actual(self):
        """
        Este método devuelve la actuación correspondiente al
        momento de hacer la llamada al método.
        Si no hay ninguna devuelve None.
        """
        hoy_ahora = datetime.datetime.today()
        assert (hoy_ahora.tzinfo is None)
        dia_semanal = hoy_ahora.weekday()
        hora_actual = hoy_ahora.time()

        # FIXME: PERFORMANCE: ver si el resultado de 'filter()' se cachea,
        # sino, usar algo que se cachee, ya que este metodo es ejecutado
        # muchas veces desde el daemon
        actuaciones_hoy = self.actuaciones.filter(dia_semanal=dia_semanal)
        if not actuaciones_hoy:
            return None

        for actuacion in actuaciones_hoy:
            if actuacion.hora_desde <= hora_actual <= actuacion.hora_hasta:
                return actuacion
        return None

    def verifica_fecha(self, hoy_ahora):
        """
        Este método se encarga de verificar si la fecha pasada como
        parametro en hoy_ahora es válida para la campaña actual.
        Devuelve True o False.
        """
        assert isinstance(hoy_ahora, datetime.datetime)

        fecha_actual = hoy_ahora.date()

        if self.fecha_inicio <= fecha_actual <= self.fecha_fin:
            return True
        return False

#    def obtener_intentos_pendientes(self):
#        """Devuelve instancias de IntentoDeContacto para los que
#        haya que intentar realizar llamadas.
#        Solo tiene sentido ejecutar este metodo en campanas activas.
#        """
#        # (a) Este metodo tambien se podria poner en IntentoDeContactoManager
#        # pero me parece mas asertado implementarlo en campaña, asi se
#        # pueden controlar cosas como el estado de la campaña, por ejemplo.
#        # (b) Otra forma sería dejar este metodo (para poder hacer controles
#        # a nivel de campaña), pero la busqueda de las instancias de
#        # IntentoDeContacto hacerlo usando IntentoDeContactoManager.
#        # Esta alternativa me gusta (cada modelo maneja su logica), pero
#        # tengo la duda de que valga la pena hacer 2 metodos en vez de 1.
#        # La ventaja es que, con esta última idea, cada modelo es
#        # manejado por si mismo, algo que puede ayudar a la mantenibilidad.
#        # DECISION: que cada modelo maneje su parte
#        #assert self.estado in [Campana.ESTADO_ACTIVA]
#        return IntentoDeContacto.objects._obtener_pendientes_de_campana(
#            self.id)
#
#    def obtener_intentos_contesto(self):
#        """
#        Devuelve instancias de IntentoDeContacto para los que
#        haya que se contesto la llamadas.
#        """
#        return IntentoDeContacto.objects._obtener_contesto_de_campana(
#            self.id)
#
#    def obtener_intentos_no_contesto(self):
#        """
#        Devuelve instancias de IntentoDeContacto para los que
#        haya que no se contesto la llamadas.
#        """
#        return IntentoDeContacto.objects._obtener_no_contesto_de_campana(
#            self.id)
#
#    def obtener_intentos_error_interno(self):
#        """
#        Devuelve instancias de IntentoDeContacto para los que
#        haya que se registro un error interno en la llamadas.
#        """
#        return IntentoDeContacto.objects._obtener_error_interno_de_campana(
#            self.id)

    TORTA_GENERAL = 'TORTA_GENERAL'
    TORTA_OPCIONES = 'TORTA_OPCIONES'
    BARRA_INTENTOS = 'BARRA_INTENTOS'
    TORTA_NO_SELECCIONO = 'TORTA_NO_SELECCIONO'
    TORTA_NO_INTENTO = 'TORTA_NO_INTENTO'
    PATH_GRAFICOS = {
        TORTA_GENERAL: '{0}/graficos/{1}-torta.svg',
        TORTA_OPCIONES: '{0}/graficos/{1}-torta-opciones.svg',
        BARRA_INTENTOS: '{0}/graficos/{1}-barra-intentos.svg',
        TORTA_NO_SELECCIONO: '{0}/graficos/{1}-torta-no-seleccionaron.svg',
        TORTA_NO_INTENTO: '{0}/graficos/{1}-torta-no-intento.svg',
    }
    URL_GRAFICOS = {
        TORTA_GENERAL: '{0}graficos/{1}-torta.svg',
        TORTA_OPCIONES: '{0}graficos/{1}-torta-opciones.svg',
        BARRA_INTENTOS: '{0}graficos/{1}-barra-intentos.svg',
        TORTA_NO_SELECCIONO: '{0}graficos/{1}-torta-no-seleccionaron.svg',
        TORTA_NO_INTENTO: '{0}graficos/{1}-torta-no-intento.svg',
    }

    @property
    def url_grafico_torta(self):
        return self._url_grafico(Campana.TORTA_GENERAL)

    @property
    def url_grafico_torta_opciones(self):
        return self._url_grafico(Campana.TORTA_OPCIONES)

    @property
    def url_grafico_barra_intentos(self):
        return self._url_grafico(Campana.BARRA_INTENTOS)

    @property
    def url_grafico_torta_no_seleccionaron(self):
        return self._url_grafico(Campana.TORTA_NO_SELECCIONO)

    @property
    def url_grafico_torta_no_intento(self):
        return self._url_grafico(Campana.TORTA_NO_INTENTO)

    def _url_grafico(self, grafico):
        """
        Devuelve la url al gráfico svg en medias files.
        """

        path = Campana.PATH_GRAFICOS[grafico].format(settings.MEDIA_ROOT,
            self.id)
        if os.path.exists(path):
            url = Campana.URL_GRAFICOS[grafico].format(settings.MEDIA_URL,
                self.id)
            return url
        return None

    def obtener_estadisticas_render_graficos_supervision(self):
        estadisticas = self.calcular_estadisticas(
            AgregacionDeEventoDeContacto.TIPO_AGREGACION_SUPERVISION)

        if estadisticas:
           #Torta: porcentajes de opciones selecionadas.
            opcion_valida_x_porcentaje = estadisticas[
                'opcion_valida_x_porcentaje']
            opcion_invalida_x_porcentaje = estadisticas[
                'opcion_invalida_x_porcentaje']

            torta_opcion_x_porcentaje = pygal.Pie(
                style=Campana.ESTILO_MULTICOLOR)
            torta_opcion_x_porcentaje.title = 'Porcentajes de opciones.'

            for opcion, porcentaje in opcion_valida_x_porcentaje.items():
                torta_opcion_x_porcentaje.add('#{0}'.format(opcion),
                    porcentaje)

            porcentaje_opciones_invalidas = 0
            for porcentaje in opcion_invalida_x_porcentaje.values():
                porcentaje_opciones_invalidas += porcentaje
            if porcentaje_opciones_invalidas:
                torta_opcion_x_porcentaje.add('Inválidas',
                    porcentaje_opciones_invalidas)

            return {
                    'estadisticas': estadisticas,
                    'torta_opcion_x_porcentaje': torta_opcion_x_porcentaje,
            }
        else:
            logger.info("Campana %s NO obtuvo estadísticas.", self.id)

    def obtener_estadisticas_render_graficos_reportes(self):
        estadisticas = self.calcular_estadisticas(
            AgregacionDeEventoDeContacto.TIPO_AGREGACION_REPORTE)

        if estadisticas:
            logger.info("Generando grafico para campana %s", self.id)

            #Torta: porcentajes de contestados, no contestados y no llamados.
            torta_general = pygal.Pie(style=Campana.ESTILO_VERDE_ROJO_NARANJA)
            torta_general.title = 'Porcentajes Generales de {0} contactos.'.\
                format(estadisticas['total_contactos'])
            torta_general.add('Atendidos', estadisticas[
                'porcentaje_atendidos'])

            torta_general.add('No Atendidos', estadisticas[
                'porcentaje_no_atendidos'])
            torta_general.add('Sin Llamar', estadisticas[
                'porcentaje_no_llamados'])

            #Torta: porcentajes de opciones selecionadas.
            dic_opcion_x_porcentaje = estadisticas['opcion_x_porcentaje']
            torta_opcion_x_porcentaje = pygal.Pie(
                style=Campana.ESTILO_MULTICOLOR)
            torta_opcion_x_porcentaje.title = 'Porcentajes de opciones.'
            for opcion, porcentaje in dic_opcion_x_porcentaje.items():
                torta_opcion_x_porcentaje.add('#{0}'.format(opcion),
                    porcentaje)

            #Barra: Total de llamados atendidos en cada intento.
            total_atendidos_intentos = estadisticas['total_atendidos_intentos']
            intentos = [total_atendidos_intentos[intentos] for intentos, _ in\
                total_atendidos_intentos.items()]
            barra_atendidos_intentos = pygal.Bar(show_legend=False,
                style=Campana.ESTILO_MULTICOLOR)
            barra_atendidos_intentos.title = 'Cantidad de llamadas atendidas en\
                cada intento.'
            barra_atendidos_intentos.x_labels = map(str, range(1,
                len(total_atendidos_intentos) + 1))
            barra_atendidos_intentos.add('Cantidad', intentos)

            return {
                'estadisticas': estadisticas,
                'torta_general': torta_general,
                'torta_opcion_x_porcentaje': torta_opcion_x_porcentaje,
                'barra_atendidos_intentos': barra_atendidos_intentos,
            }
        else:
            logger.info("Campana %s NO obtuvo estadísticas.", self.id)

    def calcular_estadisticas(self, tipo_agregacion):
        """
        Este método devuelve las estadísticas de
        la campaña actual.
        """

        #Una campana que aún no se activo, no tendria porque devolver
        #estadísticas.
        assert self.estado in (Campana.ESTADO_ACTIVA, Campana.ESTADO_PAUSADA,
            Campana.ESTADO_FINALIZADA)

        dic_totales = AgregacionDeEventoDeContacto.objects.procesa_agregacion(
            self.pk, self.cantidad_intentos, tipo_agregacion)

        total_contactos = dic_totales['total_contactos']
        if not total_contactos > 0:
            return None

        #Generales
        total_atentidos = dic_totales['total_atentidos']
        porcentaje_atendidos = float(100 * total_atentidos / total_contactos)

        total_no_atendidos = dic_totales['total_no_atendidos']
        porcentaje_no_atendidos = float(100 * total_no_atendidos / \
            total_contactos)

        total_no_llamados = dic_totales['total_no_llamados']
        porcentaje_no_llamados = float(100 * total_no_llamados / \
            total_contactos)

        # Atendidos en cada intento.
        total_atendidos_intentos = dic_totales['total_atendidos_intentos']

        # Cantidad por opción.
        opcion_x_cantidad = defaultdict(lambda: 0)
        opcion_x_porcentaje = defaultdict(lambda: 0)
        opcion_invalida_x_cantidad = defaultdict(lambda: 0)
        opcion_invalida_x_porcentaje = defaultdict(lambda: 0)
        opcion_valida_x_cantidad = defaultdict(lambda: 0)
        opcion_valida_x_porcentaje = defaultdict(lambda: 0)
        if dic_totales['total_opciones'] > 0:
            opciones_campana = [opcion.digito for opcion in\
                self.opciones.all()]
            for opcion in range(10):
                cantidad_opcion = dic_totales['total_opcion_{0}'.format(
                    opcion)]
                opcion_x_cantidad[opcion] = cantidad_opcion
                opcion_x_porcentaje[opcion] = float(100 * cantidad_opcion / \
                    dic_totales['total_opciones'])
                if not opcion in opciones_campana:
                    opcion_invalida_x_cantidad[opcion] = cantidad_opcion
                    opcion_invalida_x_porcentaje[opcion] = float(100 *
                        cantidad_opcion / dic_totales['total_opciones'])
                else:
                    opcion_valida_x_cantidad[opcion] = cantidad_opcion
                    opcion_valida_x_porcentaje[opcion] = float(100 *
                        cantidad_opcion / dic_totales['total_opciones'])

        dic_estadisticas = {
            # Estadísticas Generales.
            'total_contactos': total_contactos,

            'total_atentidos': total_atentidos,
            'porcentaje_atendidos': porcentaje_atendidos,
            'total_no_atentidos': total_no_atendidos,
            'porcentaje_no_atendidos': porcentaje_no_atendidos,
            'total_no_llamados': total_no_llamados,
            'porcentaje_no_llamados': porcentaje_no_llamados,
            'porcentaje_avance': dic_totales['porcentaje_avance'],
            'total_atendidos_intentos': total_atendidos_intentos,

            #Estadisticas de las llamadas Contestadas.
            'opcion_x_cantidad': dict(opcion_x_cantidad),
            'opcion_x_porcentaje': dict(opcion_x_porcentaje),
            'opcion_invalida_x_cantidad': dict(opcion_invalida_x_cantidad),
            'opcion_invalida_x_porcentaje': dict(opcion_invalida_x_porcentaje),
            'opcion_valida_x_cantidad': dict(opcion_valida_x_cantidad),
            'opcion_valida_x_porcentaje': dict(opcion_valida_x_porcentaje),
        }

        return dic_estadisticas

    def exportar_reporte_csv(self):
        from fts_daemon.models import EventoDeContacto

        assert self.estado == Campana.ESTADO_FINALIZADA

        dirname = 'reporte_campana'
        filename = "{0}-reporte.csv".format(self.id)
        file_path = "{0}/{1}/{2}".format(settings.MEDIA_ROOT, dirname, filename)
        file_url = "{0}/{1}/{2}".format(settings.MEDIA_URL, dirname, filename)
        if os.path.exists(file_path):
            return file_url

        dirname, filename = crear_archivo_en_media_root(dirname,
            "{0}-reporte".format(self.id), ".csv")

        values = EventoDeContacto.objects_estadisticas\
            .obtener_opciones_por_contacto(self.pk)

        with open(file_path, 'wb') as csvfile:
            csvwiter = csv.writer(csvfile)
            for telefono, lista_eventos in values:
                lista_opciones = [telefono]
                for opcion in range(9):
                    evento = EventoDeContacto.NUMERO_OPCION_MAP[opcion]
                    if evento in lista_eventos:
                        lista_opciones.append(opcion)
                    else:
                        lista_opciones.append(None)
                csvwiter.writerow(lista_opciones)
        return file_url

    def obtener_estadisticas(self):
        """
        Este método devuelve las estadísticas de
        la campaña actual.
        Podría procesarse esta información directamente en EventoDeContacto.
        """

        from fts_daemon.models import EventoDeContacto

        dic_estado_x_cantidad, dic_intento_x_contactos, dic_evento_x_cantidad = \
            EventoDeContacto.objects_estadisticas.\
            obtener_estadisticas_de_campana(self.id)

        total_contactos = dic_estado_x_cantidad[
            'finalizado_x_evento_finalizador'] + dic_estado_x_cantidad[
            'finalizado_x_limite_intentos'] + dic_estado_x_cantidad[
            'pendientes']
        cantidad_contestadas = dic_estado_x_cantidad[
            'finalizado_x_evento_finalizador']
        porcentaje_contestadas = float(100 * cantidad_contestadas / \
            total_contactos)
        cantidad_no_contestadas = dic_estado_x_cantidad[
            'finalizado_x_limite_intentos']
        porcentaje_no_contestadas = float(100 * cantidad_no_contestadas / \
            total_contactos)
        porcentaje_avance = porcentaje_contestadas + porcentaje_no_contestadas
        cantidad_pendientes = dic_estado_x_cantidad['pendientes']
        porcentaje_pendientes = float(100 * cantidad_pendientes / \
            total_contactos)
        cantidad_no_selecciono_opcion = dic_estado_x_cantidad[
            'no_selecciono_opcion']
        porcentaje_no_selecciono_opcion = float(
            100 * cantidad_no_selecciono_opcion / total_contactos)
        cantidad_selecciono_opcion = total_contactos - dic_estado_x_cantidad[
            'no_selecciono_opcion']
        porcentaje_selecciono_opcion = float(
            100 * cantidad_selecciono_opcion / total_contactos)
        cantidad_no_intentados = dic_intento_x_contactos[0]
        porcentaje_no_intentados = float(100 * cantidad_no_intentados / \
            total_contactos)
        cantidad_intentados = total_contactos - cantidad_no_intentados
        porcentaje_intentados = float(100 * cantidad_intentados / \
            total_contactos)
        #Calcula, por cada opción, la cantidad de veces seleccionada.
        opcion_x_cantidad = defaultdict(lambda: 0)

        for opcion_campana in self.opciones.all():
            evento = EventoDeContacto.NUMERO_OPCION_MAP[opcion_campana.digito]
            opcion_x_cantidad[opcion_campana.digito] += \
                dic_evento_x_cantidad.get(evento, 0)
        #Calcula la cantidad de opciones inválidas que se selecionaron.
        eventos_opciones_seleccionadas = filter(lambda evento: evento in\
            EventoDeContacto.NUMERO_OPCION_MAP.values(),
            dic_evento_x_cantidad.keys())
        eventos_opciones_campana = map(lambda opcion:\
            EventoDeContacto.NUMERO_OPCION_MAP[opcion.digito],
            self.opciones.all())
        opcion_invalida_x_cantidad = defaultdict(lambda: 0)
        for evento in set(eventos_opciones_seleccionadas):
            if not evento in eventos_opciones_campana:
                opcion_invalida = '{0} (Inválida)'.format(
                    EventoDeContacto.EVENTO_A_NUMERO_OPCION_MAP[evento])
                opcion_invalida_x_cantidad[opcion_invalida] += 1
        #Calcula, por cada opción el porcentaje que representa.
        opcion_valida_invalida_x_cantidad = {}
        opcion_valida_invalida_x_cantidad.update(opcion_x_cantidad)
        opcion_valida_invalida_x_cantidad.update(opcion_invalida_x_cantidad)
        total_opciones = sum(opcion_valida_invalida_x_cantidad.values())
        opcion_x_porcentaje = defaultdict(lambda: 0)
        if total_opciones:
            for opcion, cantidad in\
                opcion_valida_invalida_x_cantidad.items():
                opcion_x_porcentaje[opcion] += float(100 * cantidad / \
                total_opciones)
        return {

            #Estadisticas Generales.
            'total_contactos': total_contactos,
            'cantidad_contestadas': cantidad_contestadas,
            'porcentaje_contestadas': porcentaje_contestadas,
            'cantidad_no_contestadas': cantidad_no_contestadas,
            'porcentaje_no_contestadas': porcentaje_no_contestadas,
            'porcentaje_avance': porcentaje_avance,
            'cantidad_pendientes': cantidad_pendientes,
            'porcentaje_pendientes': porcentaje_pendientes,
            'cantidad_selecciono_opcion': cantidad_selecciono_opcion,
            'porcentaje_selecciono_opcion': porcentaje_selecciono_opcion,
            'cantidad_no_selecciono_opcion': cantidad_no_selecciono_opcion,
            'porcentaje_no_selecciono_opcion': porcentaje_no_selecciono_opcion,
            'cantidad_intentados': cantidad_intentados,
            'porcentaje_intentados': porcentaje_intentados,
            'cantidad_no_intentados': cantidad_no_intentados,
            'porcentaje_no_intentados': porcentaje_no_intentados,
            'dic_intento_x_contactos': dict(dic_intento_x_contactos),
            #Estadisticas de las llamadas Contestadas.
            'opcion_x_cantidad': dict(opcion_x_cantidad),
            'opcion_invalida_x_cantidad': dict(opcion_invalida_x_cantidad),
            'opcion_x_porcentaje': dict(opcion_x_porcentaje),
        }

    def _genera_graficos_estadisticas(self):
        """
        Genera el gráfico torta de los intentos de contacto de la
        campaña finalizada.
        """
        #Obtiene estadística.
        estadisticas = self.obtener_estadisticas()

        if estadisticas:
            logger.info("Generando grafico para campana %s", self.id)

            path_torta = Campana.PATH_GRAFICOS[Campana.TORTA_GENERAL].format(
                settings.MEDIA_ROOT, self.id)

            path_torta_opciones = Campana.PATH_GRAFICOS[Campana.TORTA_OPCIONES]\
                .format(settings.MEDIA_ROOT, self.id)

            path_barra_contactos_x_intentos = \
                Campana.PATH_GRAFICOS[Campana.BARRA_INTENTOS].format(
                settings.MEDIA_ROOT, self.id)

            path_torta_no_selecciono = \
                Campana.PATH_GRAFICOS[Campana.TORTA_NO_SELECCIONO]\
                .format(settings.MEDIA_ROOT, self.id)

            path_torta_no_intentados = \
                Campana.PATH_GRAFICOS[Campana.TORTA_NO_INTENTO]\
                .format(settings.MEDIA_ROOT, self.id)

            graficos_dir = '{0}/graficos/'.format(settings.MEDIA_ROOT)
            if not os.path.exists(graficos_dir):
                try:
                    os.mkdir(graficos_dir, 0755)
                except OSError:
                    logger.warn("Error al intentar crear directorio para "
                        "graficos: %s (se ignorara el error)", graficos_dir)

            #Torta: porcentajes de contestados, no contestados y pendientes.
            pie_chart = pygal.Pie(style=Campana.ESTILO_VERDE_ROJO_NARANJA)
            pie_chart.title = 'Porcentajes generales.'
            pie_chart.add('Contestados', estadisticas['porcentaje_contestadas'])
            pie_chart.add('No Contestados', estadisticas[
                'porcentaje_no_contestadas'])
            pie_chart.add('Pendientes', estadisticas['porcentaje_pendientes'])
            pie_chart.render_to_file(path_torta)

            #Torta: porcentajes de opciones selecionadas.
            dic_opcion_x_porcentaje = estadisticas['opcion_x_porcentaje']
            pie_chart = pygal.Pie(style=Campana.ESTILO_MULTICOLOR)
            pie_chart.title = 'Porcentajes opciones seleccionadas.'
            for opcion, porcentaje in dic_opcion_x_porcentaje.items():
                pie_chart.add('#{0}'.format(opcion), porcentaje)
            pie_chart.render_to_file(path_torta_opciones)

            #Barra: intentos x cantidad contactos.
            dic_intento_x_contactos = estadisticas['dic_intento_x_contactos']
            intentos = [dic_intento_x_contactos[intentos] for intentos, _ in\
                dic_intento_x_contactos.items()]
            line_chart = pygal.Bar(show_legend=False,
                style=Campana.ESTILO_MULTICOLOR)
            line_chart.title = 'Cantidad de contactos por número de intentos.'
            line_chart.x_labels = map(str, range(0,
                len(dic_intento_x_contactos)))
            line_chart.add('Cantidad', intentos)
            line_chart.render_to_file(path_barra_contactos_x_intentos)

            #Torta: porcentajes de Contactos que seleccionaron y
            #no seleccionaron alguna opción.
            pie_chart = pygal.Pie(style=Campana.ESTILO_VERDE_ROJO_NARANJA)
            pie_chart.title = 'Porcentaje contactos que seleccionaron y no'\
                'seleccionaron opciones.'
            pie_chart.add('Seleccionaron', estadisticas[
                'porcentaje_selecciono_opcion'])
            pie_chart.add('No Seleccionaron', estadisticas[
                'porcentaje_no_selecciono_opcion'])
            pie_chart.render_to_file(path_torta_no_selecciono)

            #Torta: porcentajes de Contactos Llamados y No Llamados.
            pie_chart = pygal.Pie(style=Campana.ESTILO_VERDE_ROJO_NARANJA)
            pie_chart.title = \
                'Porcentaje contactos con intentos y sin intento de llamdas.'
            pie_chart.add('Con Intento', estadisticas[
                'porcentaje_intentados'])
            pie_chart.add('Sin Intento', estadisticas[
                'porcentaje_no_intentados'])
            pie_chart.render_to_file(path_torta_no_intentados)
        else:
            logger.info("Ignorando campana %s (total_contactos == 0)", self.id)

    def __unicode__(self):
        return self.nombre

    def get_nombre_contexto_para_asterisk(self):
        """Devuelve un texto para ser usado en Asterisk,
        para nombrar el contexto asociado a la campana.
        """
        assert self.id
        return 'campania_{0}'.format(self.id)

    def clean(self):
        """
        Valida que al crear una campaña la fechas de
        inicialización sea menor o igual a la fecha de
        finalización.
        """
        fecha_hoy = datetime.date.today()
        if self.fecha_inicio and self.fecha_fin:
            if self.fecha_inicio > self.fecha_fin:
                raise ValidationError({
                    'fecha_inicio': ["La fecha de inicio debe ser\
                        menor o igual a la fecha de finalización."],
                    'fecha_fin': ["La fecha de inicio debe ser\
                        mayor o igual a la fecha de finalización."],
                })
            elif self.fecha_inicio < fecha_hoy:
                raise ValidationError({
                    'fecha_inicio': ["La fecha de inicio debe ser\
                        mayor o igual a la fecha actual."],
                })

        cantidad_contactos = self.bd_contacto.get_cantidad_contactos()
        if not self.cantidad_canales < cantidad_contactos:
            raise ValidationError({
                    'cantidad_canales': ["La cantidad de canales debe ser\
                        menor a la cantidad de contactos de la base de datos."]
                })

#==============================================================================
# AgregacionDeEventoDeContacto
#==============================================================================


class AgregacionDeEventoDeContactoManager(models.Manager):
    def establece_agregacion(self, campana_id, cantidad_intentos,
        tipo_agregacion, timestamp_ultimo_evento=None):
        """
        Se encarga de obtener los contadores de eventos por cada intento de
        contacto de la campaña, y es establecer los registros de ADEDC
        para cada intento de la campaña con los datos de los contadores.
        :param campana_id: De que campana se establece los registros de ADEDC.
        :type campana_id: int
        :param cantidad_intentos: El limite de intentos para la campana.
        :type cantidad_intentos: int
        """
        from fts_daemon.models import EventoDeContacto

        #Obtenemos los contadores por intentos.
        dic_contadores_x_intentos = EventoDeContacto.objects_estadisticas.\
            obtener_contadores_por_intento(campana_id, cantidad_intentos,
                timestamp_ultimo_evento)

        if not dic_contadores_x_intentos:
            return None

        #Por cada intento en el diccionario dic_contadores_x_intentos,
        #actualizamos o generamos según exista o no el registro con las
        #cantidades de cada intento.
        for numero_intento, dic_contadores in dic_contadores_x_intentos.items():

            dic_opciones = dict((opcion, 0) for opcion in range(10))
            for dic_evento_cantidad in dic_contadores['cantidad_x_opcion']:
                opcion = EventoDeContacto.EVENTO_A_NUMERO_OPCION_MAP[
                        dic_evento_cantidad['evento']]
                dic_opciones.update({opcion: dic_evento_cantidad[
                    'cantidad']})

            agregacion_evento_contacto, created = self.get_or_create(
                campana_id=campana_id, numero_intento=numero_intento)

            if created:
                agregacion_evento_contacto.cantidad_intentos = \
                    dic_contadores['cantidad_intentos']
                agregacion_evento_contacto.cantidad_finalizados = \
                    dic_contadores['cantidad_finalizados']
                agregacion_evento_contacto.cantidad_opcion_0 = dic_opciones[0]
                agregacion_evento_contacto.cantidad_opcion_1 = dic_opciones[1]
                agregacion_evento_contacto.cantidad_opcion_2 = dic_opciones[2]
                agregacion_evento_contacto.cantidad_opcion_3 = dic_opciones[3]
                agregacion_evento_contacto.cantidad_opcion_4 = dic_opciones[4]
                agregacion_evento_contacto.cantidad_opcion_5 = dic_opciones[5]
                agregacion_evento_contacto.cantidad_opcion_6 = dic_opciones[6]
                agregacion_evento_contacto.cantidad_opcion_7 = dic_opciones[7]
                agregacion_evento_contacto.cantidad_opcion_8 = dic_opciones[8]
                agregacion_evento_contacto.cantidad_opcion_9 = dic_opciones[9]

            else:
                agregacion_evento_contacto.cantidad_intentos += \
                    dic_contadores['cantidad_intentos']
                agregacion_evento_contacto.cantidad_finalizados += \
                    dic_contadores['cantidad_finalizados']
                agregacion_evento_contacto.cantidad_opcion_0 += dic_opciones[0]
                agregacion_evento_contacto.cantidad_opcion_1 += dic_opciones[1]
                agregacion_evento_contacto.cantidad_opcion_2 += dic_opciones[2]
                agregacion_evento_contacto.cantidad_opcion_3 += dic_opciones[3]
                agregacion_evento_contacto.cantidad_opcion_4 += dic_opciones[4]
                agregacion_evento_contacto.cantidad_opcion_5 += dic_opciones[5]
                agregacion_evento_contacto.cantidad_opcion_6 += dic_opciones[6]
                agregacion_evento_contacto.cantidad_opcion_7 += dic_opciones[7]
                agregacion_evento_contacto.cantidad_opcion_8 += dic_opciones[8]
                agregacion_evento_contacto.cantidad_opcion_9 += dic_opciones[9]

            agregacion_evento_contacto.tipo_agregacion = tipo_agregacion
            agregacion_evento_contacto.timestamp_ultimo_evento = dic_contadores[
                'timestamp_ultimo_evento']

            agregacion_evento_contacto.save()

    def procesa_agregacion(self, campana_id, cantidad_intentos,
        tipo_agregacion):
        """
        Sumariza los contadores de cada intento de contacto de la campana.
        :param campana_id: De que campana que se sumarizaran los contadores.
        :type campana_id: int
        """

        campana = Campana.objects.get(pk=campana_id)
        limite_intentos = campana.cantidad_intentos
        total_contactos = campana.bd_contacto.get_cantidad_contactos()
        dic_totales = {
            'limite_intentos': limite_intentos,
            'total_contactos': total_contactos,
        }

        if total_contactos:
            try:
                ultima_agregacion_campana = self.get(campana_id=campana_id,
                    numero_intento=cantidad_intentos)
                # Si la obtención de ultima_agregacion_campana no da excepción
                # quiere decir que ya se generaron los registros de agregación
                # para la campana y hay que actualizarlos desde el último
                # evento hasta hoy y ahora.
                try:
                    timestamp_ultimo_evento = \
                        ultima_agregacion_campana.timestamp_ultimo_evento

                    assert all(agregacion.timestamp_ultimo_evento ==
                        timestamp_ultimo_evento for agregacion in self.filter(
                        campana_id=campana_id)),\
                        """Los timestamp_ultimo_evento no son iguales para
                        todos los registros de AgregacionDeEventoDeContacto
                        para la Campana {0}.""".format(campana_id)
                    self.establece_agregacion(campana_id, cantidad_intentos,
                        tipo_agregacion, timestamp_ultimo_evento)
                except:
                    # FIXME: Ver solución para cuándo se desata el assert.
                    # Ocurre cuándo se actualiza (F5) el template de manera
                    # muy seguida.
                    pass

            except AgregacionDeEventoDeContacto.DoesNotExist:
                # Si la obtención de ultima_agregacion_campana da excepción
                # quiere decir que es la primera vez que se quiere ver el
                # Reporte o la Supervisión y no está generados los registros
                # de agregacion para la campana. Se generan los registros sin
                # tener en cuenta un timestamp, toma todos los eventos de
                # EventoDeContacto para la campana.
                self.establece_agregacion(campana_id, cantidad_intentos,
                    tipo_agregacion)

            agregaciones_campana = self.filter(campana_id=campana_id)

            dic_totales.update(agregaciones_campana.aggregate(
                total_intentados=Sum('cantidad_intentos'),
                total_atentidos=Sum('cantidad_finalizados'),
                total_opcion_0=Sum('cantidad_opcion_0'),
                total_opcion_1=Sum('cantidad_opcion_1'),
                total_opcion_2=Sum('cantidad_opcion_2'),
                total_opcion_3=Sum('cantidad_opcion_3'),
                total_opcion_4=Sum('cantidad_opcion_4'),
                total_opcion_5=Sum('cantidad_opcion_5'),
                total_opcion_6=Sum('cantidad_opcion_6'),
                total_opcion_7=Sum('cantidad_opcion_7'),
                total_opcion_8=Sum('cantidad_opcion_8'),
                total_opcion_9=Sum('cantidad_opcion_9'))
            )

            total_no_llamados = total_contactos - dic_totales[
                'total_intentados']
            if total_no_llamados < 0:
                total_no_llamados = 0

            total_no_atendidos = total_contactos - (total_no_llamados +
                dic_totales['total_atentidos'])

            total_opciones = 0
            for opcion in range(10):
                total_opciones += dic_totales['total_opcion_{0}'.format(
                    opcion)]

            total_atendidos_intentos = dict((agregacion_campana.numero_intento,
                agregacion_campana.cantidad_finalizados)
                for agregacion_campana in agregaciones_campana)

            finalizados = 0
            for agregacion_campana in agregaciones_campana:
                finalizados += agregacion_campana.cantidad_finalizados

                finalizados_limite = 0
                if agregacion_campana == limite_intentos:
                    if agregacion_campana.cantidad_intentos >\
                        agregacion_campana.cantidad_finalizados:
                        finalizados_limite =\
                            (agregacion_campana.cantidad_intentos -
                            agregacion_campana.cantidad_finalizados)

                porcentaje_avance = float(100 * (finalizados +
                        finalizados_limite) / total_contactos)

            dic_totales.update({
                'total_no_llamados': total_no_llamados,
                'total_no_atendidos': total_no_atendidos,
                'total_opciones': total_opciones,
                'total_atendidos_intentos': total_atendidos_intentos,
                'porcentaje_avance': porcentaje_avance})
        return dic_totales


class AgregacionDeEventoDeContacto(models.Model):
    """
    Representa los contadores de EventoDeContacto para
    *cada grupo de intentos* de llamadas de una Campana.
    Por lo que si una Campana tiene un limite de 2 intentos
    para cada contacto, esa campana debería tener 2 registros
    con las cantidades, de ciertos eventos, de ese intento.
    """
    TIPO_AGREGACION_SUPERVISION = 1
    TIPO_AGREGACION_REPORTE = 2
    TIPO_AGREGACION_DEPURACION = 3

    objects = AgregacionDeEventoDeContactoManager()

    campana_id = models.IntegerField(db_index=True)
    numero_intento = models.IntegerField()
    cantidad_intentos = models.IntegerField(null=True)
    cantidad_finalizados = models.IntegerField(null=True)
    cantidad_opcion_0 = models.IntegerField(null=True)
    cantidad_opcion_1 = models.IntegerField(null=True)
    cantidad_opcion_2 = models.IntegerField(null=True)
    cantidad_opcion_3 = models.IntegerField(null=True)
    cantidad_opcion_4 = models.IntegerField(null=True)
    cantidad_opcion_5 = models.IntegerField(null=True)
    cantidad_opcion_6 = models.IntegerField(null=True)
    cantidad_opcion_7 = models.IntegerField(null=True)
    cantidad_opcion_8 = models.IntegerField(null=True)
    cantidad_opcion_9 = models.IntegerField(null=True)
    timestamp_ultima_actualizacion = models.DateTimeField(auto_now_add=True)
    timestamp_ultimo_evento = models.DateTimeField(null=True)
    tipo_agregacion = models.IntegerField(null=True)

    def __unicode__(self):
        return "AgregacionDeEventoDeContacto-{0}-{1}".format(
            self.campana_id, self.numero_intento)


##============================================================================
## IntentoDeContacto
##============================================================================
#
#class IntentoDeContactoManager(models.Manager):
#    """Manager para el modelo IntentoDeContacto"""
#
#    def _obtener_pendientes_de_campana(self, campana_id):
#        """Devuelve QuerySet con intentos pendientes de una campana, ignora
#        completamente las cuestiones de la campaña, como su estado.
#
#        Esto es parte de la API interna, y no deberia usarse directamente
#        nada más que desde otros Managers.
#
#        Para buscar intentos pendientes de una campaña, usar:
#            Campana.obtener_intentos_pendientes()
#        """
#        raise NotImplementedError()
#
#    def _obtener_no_contesto_de_campana(self, campana_id):
#        """Devuelve QuerySet con intentos no contestados de una campana,
#        ignora completamente las cuestiones de la campaña, como su estado.
#
#        Esto es parte de la API interna, y no deberia usarse directamente
#        nada más que desde otros Managers.
#
#        Para buscar intentos no contestados de una campaña, usar:
#            Campana.obtener_intentos_no_contestados()
#        """
#        raise NotImplementedError()
#
#    def _obtener_contesto_de_campana(self, campana_id):
#        """Devuelve QuerySet con intentos contestados de una campana, ignora
#        completamente las cuestiones de la campaña, como su estado.
#
#        Esto es parte de la API interna, y no deberia usarse directamente
#        nada más que desde otros Managers.
#
#        Para buscar intentos no contestados de una campaña, usar:
#            Campana.obtener_intentos_contestados()
#        """
#        raise NotImplementedError()
#
#    def _obtener_error_interno_de_campana(self, campana_id):
#        """Devuelve QuerySet con intentos erroneos de una campana, ignora
#        completamente las cuestiones de la campaña, como su estado.
#
#        Esto es parte de la API interna, y no deberia usarse directamente
#        nada más que desde otros Managers.
#
#        Para buscar intentos no contestados de una campaña, usar:
#            Campana.obtener_intentos_error_interno()
#        """
#        raise NotImplementedError()
#
#    def update_estado_por_originate(self, intento_id, originate_ok):
#        """Actualiza el estado del intento, dependiendo del resultado
#        del comando originate.
#        """
#        raise NotImplementedError()
#


#==============================================================================
# Opciones
#==============================================================================

class Opcion(models.Model):
    """
    Representa una Opción a marcar en la llamada.
    Cada opción realiza una acción concreta. Por
    ejemplo, derivar la llamada a un agente.
    """

    """Considero opciones solo del 0 a 9"""
    (CERO, UNO, DOS, TRES, CUATRO,
    CINCO, SEIS, SIETE, OCHO, NUEVE) = range(0, 10)
    DIGITO_CHOICES = (
        (CERO, '0'),
        (UNO, '1'),
        (DOS, '2'),
        (TRES, '3'),
        (CUATRO, '4'),
        (CINCO, '5'),
        (SEIS, '6'),
        (SIETE, '7'),
        (OCHO, '8'),
        (NUEVE, '9'),
    )
    digito = models.PositiveIntegerField(
        choices=DIGITO_CHOICES,
    )

    DERIVAR = 0
    """Deriva la llamada. Ejemplo Grupo Atencion."""

    CALIFICAR = 1
    """Estable una calificación a la llamada."""

    VOICEMAIL = 2
    """Habilita para dejar un mensaje de voz."""

    REPETIR = 3
    """Repetir el mensaje."""

    ACCION_CHOICES = (
        (DERIVAR, 'DERIVAR'),
        (CALIFICAR, 'CALIFICAR'),
        (REPETIR, 'REPETIR'),
    )
    accion = models.PositiveIntegerField(
        choices=ACCION_CHOICES,
    )

    grupo_atencion = models.ForeignKey(
        'GrupoAtencion',
        null=True, blank=True,
    )
    calificacion = models.ForeignKey(
        'Calificacion',
        null=True, blank=True,
    )
    campana = models.ForeignKey(
        'Campana',
        related_name='opciones'
    )

    def __unicode__(self):
        return "Campaña {0} - Opción: {1}".format(
            self.campana,
            self.digito,
        )

    class Meta:
        #unique_together = ("digito", "campana")
        unique_together = (
            ("digito", "campana"),
            ("accion", "campana", "grupo_atencion"),
            ("accion", "campana", "calificacion"),
        )


#==============================================================================
# Actuaciones
#==============================================================================

class Actuacion(models.Model):
    """
    Representa los días de la semana y los
    horarios en que una campaña se ejecuta.
    """

    """Dias de la semana, compatibles con datetime.date.weekday()"""
    LUNES = 0
    MARTES = 1
    MIERCOLES = 2
    JUEVES = 3
    VIERNES = 4
    SABADO = 5
    DOMINGO = 6

    DIA_SEMANAL_CHOICES = (
        (LUNES, 'LUNES'),
        (MARTES, 'MARTES'),
        (MIERCOLES, 'MIERCOLES'),
        (JUEVES, 'JUEVES'),
        (VIERNES, 'VIERNES'),
        (SABADO, 'SABADO'),
        (DOMINGO, 'DOMINGO'),
    )
    dia_semanal = models.PositiveIntegerField(
        choices=DIA_SEMANAL_CHOICES,
    )

    hora_desde = models.TimeField()
    hora_hasta = models.TimeField()

    campana = models.ForeignKey(
        'Campana',
        related_name='actuaciones'
    )

    def __unicode__(self):
        return "Campaña {0} - Actuación: {1}".format(
            self.campana,
            self.get_dia_semanal_display(),
        )

    def verifica_actuacion(self, hoy_ahora):
        """
        Este método verifica que el día de la semana y la hora
        pasada en el parámetro hoy_ahora sea válida para la
        actuación actual.
        Devuelve True o False.
        """

        assert isinstance(hoy_ahora, datetime.datetime)

        dia_semanal = hoy_ahora.weekday()
        hora_actual = datetime.time(
            hoy_ahora.hour, hoy_ahora.minute, hoy_ahora.second)

        if not self.dia_semanal == dia_semanal:
            return False

        if not self.hora_desde <= hora_actual <= self.hora_hasta:
            return False

        return True

    def dia_concuerda(self, fecha_a_chequear):
        """Este método evalua si el dia de la actuacion actual `self`
        concuerda con el dia de la semana de la fecha pasada por parametro.

        :param fecha_a_chequear: fecha a chequear
        :type fecha_a_chequear: `datetime.date`
        :returns: bool - True si la actuacion es para el mismo dia de
                  la semana que el dia de la semana de `fecha_a_chequear`
        """
        # NO quiero que funcione con `datatime` ni ninguna otra
        #  subclase, más que específicamente `datetime.date`,
        #  por eso no uso `isinstance()`.
        assert type(fecha_a_chequear) == datetime.date

        return self.dia_semanal == fecha_a_chequear.weekday()

    def es_anterior_a(self, time_a_chequear):
        """Este método evalua si el rango de tiempo de la actuacion
        actual `self` es anterior a la hora pasada por parametro.
        Verifica que sea 'estrictamente' anterior, o sea, ambas horas
        de la Actuacion deben ser anteriores a la hora a chequear
        para que devuelva True.

        :param time_a_chequear: hora a chequear
        :type time_a_chequear: `datetime.time`
        :returns: bool - True si ambas horas de la actuacion son anteriores
                  a la hora pasada por parametro `time_a_chequear`.
        """
        # NO quiero que funcione con ninguna subclase, más que
        #  específicamente `datetime.time`, por eso no uso `isinstance()`.
        assert type(time_a_chequear) == datetime.time

        # Es algo redundante chequear ambos, pero bueno...
        return self.hora_desde < time_a_chequear and \
            self.hora_hasta < time_a_chequear

    def clean(self):
        """
        Valida que al crear una actuación a una campaña
        no exista ya una actuación en el rango horario
        especificado y en el día semanal seleccionado.
        """
        if self.hora_desde and self.hora_hasta:
            if self.hora_desde >= self.hora_hasta:
                raise ValidationError({
                    'hora_desde': ["La hora desde debe ser\
                        menor o igual a la hora hasta."],
                    'hora_hasta': ["La hora hasta debe ser\
                        mayor a la hora desde."],
                })

            conflicto = self.campana.actuaciones.filter(
                dia_semanal=self.dia_semanal,
                hora_desde__lte=self.hora_hasta,
                hora_hasta__gte=self.hora_desde,
            )
            if any(conflicto):
                raise ValidationError({
                    'hora_desde': ["Ya esta cubierto el rango horario\
                        en ese día semanal."],
                    'hora_hasta': ["Ya esta cubierto el rango horario\
                        en ese día semanal."],
                })


#==============================================================================
# Calificacion
#==============================================================================

class Calificacion(models.Model):
    """
    Representa una Calificacion
    """
    nombre = models.CharField(
        max_length=64,
    )
    campana = models.ForeignKey(
        'Campana',
        related_name='calificaciones'
    )

    def __unicode__(self):
        return self.nombre

    class Meta:
        ordering = ['nombre']
