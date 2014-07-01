# -*- coding: utf-8 -*-

"""
Modelos de la aplicación
"""

from __future__ import unicode_literals

from collections import defaultdict
import csv
import datetime
import logging
import math
import os

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models, transaction, connection
from django.db.models import Sum, Q
from django.utils.timezone import now
from fts_web.utiles import crear_archivo_en_media_root, upload_to, log_timing
from fts_web.errors import (FtsRecicladoCampanaError, 
    FtsRecicladoBaseDatosContactoError)

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

    def reciclar_base_datos(self, campana_id, tipo_reciclado):
        """
        Este método hace el reciclado de la base de datos según el tipo
        de reciclado seleccionado, devuelve la base de datos que usará la
        campaña reciclada.
        Parametros:
        - campana_id: El id de la campana que se está reciclado.
        - tipo_reciclado: EL tipo de reciclado que se desea realizar sobre la
        campana.
        """

        campana = Campana.objects.get(pk=campana_id)

        if int(tipo_reciclado) == Campana.TIPO_RECICLADO_TOTAL:
            return campana.bd_contacto

        elif int(tipo_reciclado) == Campana.TIPO_RECICLADO_PENDIENTES:
            # Trae los contatos telefónicos pendientes.
            lista_contactos_pendientes = campana.obtener_contactos_pendientes()

            if not lista_contactos_pendientes:
                logger.warn("El reciclado de base datos no arrojo contactos.")
                raise FtsRecicladoBaseDatosContactoError("""No se registraron
                    contactos PENDIENTES en el reciclado de la base de 
                    datos.""")

            try:
                bd_contacto = BaseDatosContacto.objects.create(
                    nombre='{0} (reciclada)'.format(
                        campana.bd_contacto.nombre),
                    archivo_importacion=campana.bd_contacto.\
                        archivo_importacion,
                    nombre_archivo_importacion=campana.bd_contacto.\
                        nombre_archivo_importacion,
                )
            except Exception, e:
                logger.warn("Se produjo un error al intentar crear la base de"
                    " datos. Exception: %s", e)
                raise FtsRecicladoBaseDatosContactoError("""No se pudo crear
                    la base datos contactos reciclada.""")
            else:
                bd_contacto.genera_contactos(lista_contactos_pendientes)
                bd_contacto.define()
                return bd_contacto

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

    def genera_contactos(self, lista_telefonos):
        """
        Este metodo se encarga de realizar la generación de contactos
        a partir de una lista de tuplas de teléfonos.
        Parametros:
        - lista_telefonos: lista de tuplas con lo números telefónicos 
        que representarán las instancias de contacto.
        """

        for telefono in lista_telefonos:
            Contacto.objects.create(
                telefono=telefono[0],
                bd_contacto=self,
            )
        self.cantidad_contactos = len(lista_telefonos)

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
        """Devuelve queryset para filtrar campañas en estado finalizadas."""
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

    def reciclar_campana(self, campana_id, bd_contacto):
        """
        Este método replica la campana pasada por parámetro con fin de
        reciclar la misma.
        """
        try:
            campana = self.get(pk=campana_id)
            assert campana.estado == Campana.ESTADO_FINALIZADA

        except Campana.DoesNotExist:
            logger.warn("No se pudo recuperar la Campana: %s", campana_id)
            raise FtsRecicladoCampanaError("No se pudo recuperar la Campaña.")
        else:
            # Replica Campana.
            campana_reciclada = self.create(
                nombre='{0} (reciclada)'.format(campana.nombre),
                cantidad_canales=campana.cantidad_canales,
                cantidad_intentos=campana.cantidad_intentos,
                segundos_ring=campana.segundos_ring,
                fecha_inicio=campana.fecha_inicio,
                fecha_fin=campana.fecha_fin,
                audio_original=campana.audio_original,
                audio_asterisk=campana.audio_asterisk,
                bd_contacto=bd_contacto,
            )

            # Replica Opciones y Calificaciones.
            opciones = campana.opciones.all()
            for opcion in opciones:
                calificacion_reciclada = None
                if opcion.calificacion:
                    calificacion_reciclada = Calificacion.objects.create(
                        nombre=opcion.calificacion.nombre,
                        campana=campana_reciclada,
                    )

                Opcion.objects.create(
                    digito=opcion.digito,
                    accion=opcion.accion,
                    grupo_atencion=opcion.grupo_atencion,
                    calificacion=calificacion_reciclada,
                    campana=campana_reciclada,              
                )

            # Replica Actuaciones.
            actuaciones = campana.actuaciones.all()
            for actuacion in actuaciones:
                Actuacion.objects.create(
                    dia_semanal=actuacion.dia_semanal,
                    hora_desde=actuacion.hora_desde,
                    hora_hasta=actuacion.hora_hasta,
                    campana=campana_reciclada,
                )

        return campana_reciclada

upload_to_audios_asterisk = upload_to("audios_asterisk", 95)
upload_to_audios_originales = upload_to("audios_reproduccion", 95)


class Campana(models.Model):
    """Una campaña del call center"""

    objects = CampanaManager()

    TIPO_RECICLADO_TOTAL = 1
    TIPO_RECICLADO_PENDIENTES = 2

    TIPO_RECICLADO = (
        (TIPO_RECICLADO_TOTAL, 'TOTAL'),
        (TIPO_RECICLADO_PENDIENTES, 'PENDIENTES'),
    )

    ESTILO_VERDE_ROJO_NARANJA = Style(
        background='transparent',
        plot_background='transparent',
        foreground='#555',
        foreground_light='#555',
        foreground_dark='#555',
        opacity='1',
        opacity_hover='.6',
        transition='400ms ease-in',
        colors=('#5cb85c', '#d9534f', '#f0ad4e')
    )

    ESTILO_MULTICOLOR = Style(
        background='transparent',
        plot_background='transparent',
        foreground='#555',
        foreground_light='#555',
        foreground_dark='#555',
        opacity='1',
        opacity_hover='.6',
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
        """
        Setea la campaña como ACTIVA
        Genera los IntentoDeContacto asociados a esta campaña.
        Genera tantas instancias para AgregacionDeEventoDeContacto como
        cantidad_intentos tenga esta campaña.
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

        timestamp_ultimo_evento = now()
        for numero_intento in range(1, self.cantidad_intentos + 1):
            AgregacionDeEventoDeContacto.objects.create(
                campana_id=self.pk, numero_intento=numero_intento,
                timestamp_ultimo_evento=timestamp_ultimo_evento)

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

    def obtener_estadisticas_render_graficos_supervision(self):
        estadisticas = self.calcular_estadisticas(
            AgregacionDeEventoDeContacto.TIPO_AGREGACION_SUPERVISION)

        if estadisticas:
            # Torta: porcentajes de opciones selecionadas.
            opcion_valida_x_porcentaje = estadisticas[
                'opcion_valida_x_porcentaje']
            opcion_invalida_x_porcentaje = estadisticas[
                'opcion_invalida_x_porcentaje']

            no_data_text = "No se han seleccionado opciones"
            torta_opcion_x_porcentaje = pygal.Pie(  # @UndefinedVariable
                style=Campana.ESTILO_MULTICOLOR,
                legend_at_bottom=True,
                no_data_text=no_data_text,
                no_data_font_size=32
            )
            torta_opcion_x_porcentaje.title = 'Porcentajes de opciones.'

            opciones_dict = dict([(op.digito, op.get_descripcion_de_opcion())
                for op in self.opciones.all()])
            for opcion, porcentaje in opcion_valida_x_porcentaje.items():
                torta_opcion_x_porcentaje.add(opciones_dict[opcion],
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
        assert self.estado == Campana.ESTADO_FINALIZADA, \
            "Solo se generan reportes de campanas finalizadas"
        estadisticas = self.calcular_estadisticas(
            AgregacionDeEventoDeContacto.TIPO_AGREGACION_REPORTE)

        if estadisticas:
            logger.info("Generando grafico para campana %s", self.id)

            #Torta: porcentajes de contestados, no contestados y no llamados.
            torta_general = pygal.Pie(  # @UndefinedVariable
                style=Campana.ESTILO_VERDE_ROJO_NARANJA)
            #torta_general.title = 'Porcentajes Generales de {0} contactos.'.\
            #    format(estadisticas['total_contactos'])
            torta_general.title = "Resultado de llamadas"
            torta_general.add('Atendidas', estadisticas[
                'porcentaje_atendidos'])

            torta_general.add('No Atendidas', estadisticas[
                'porcentaje_no_atendidos'])
            torta_general.add('Sin Llamar', estadisticas[
                'porcentaje_no_llamados'])

            # Torta: porcentajes de opciones selecionadas.
            no_data_text = "No se han seleccionado opciones"
            dic_opcion_x_porcentaje = estadisticas['opcion_x_porcentaje']
            torta_opcion_x_porcentaje = pygal.Pie(  # @UndefinedVariable
                style=Campana.ESTILO_MULTICOLOR,
                legend_at_bottom=True,
                no_data_text=no_data_text,
                no_data_font_size=32
            )
            torta_opcion_x_porcentaje.title = 'Opciones seleccionadas'

            opciones_dict = dict([(op.digito, op.get_descripcion_de_opcion())
                for op in self.opciones.all()])

            for opcion, porcentaje in dic_opcion_x_porcentaje.items():
                try:
                    torta_opcion_x_porcentaje.add(opciones_dict[opcion],
                        porcentaje)
                except KeyError:
                    torta_opcion_x_porcentaje.add(
                        '#{0} N/A'.format(opcion),
                            porcentaje)

            #Barra: Total de llamados atendidos en cada intento.
            total_atendidos_intentos = estadisticas['total_atendidos_intentos']
            intentos = [total_atendidos_intentos[intentos] for intentos, _ in\
                total_atendidos_intentos.items()]
            barra_atendidos_intentos = pygal.Bar(  # @UndefinedVariable
                show_legend=False,
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

    def obtener_detalle_opciones_seleccionadas(self):
        """
        Este método se encarga de invocar al método de EDC que filtra los
        contactos por cada opción seleccionada. Devuelve un lista de
        listas por ejemplo:
        [[Opcion, [3513368309, 3513368308]], [9, [3513368309, 3513368308]]].
        """
        from fts_daemon.models import EventoDeContacto

        detalle_opciones = [list(detalle_opcion) for detalle_opcion in
            EventoDeContacto.objects_estadisticas.\
            obtener_contactos_por_opciones(self.pk)]

        opciones = Opcion.objects.filter(campana=self)

        for detalle_opcion in detalle_opciones:
            digito = EventoDeContacto.EVENTO_A_NUMERO_OPCION_MAP[
                    detalle_opcion[0]]
            try:
                opcion = opciones.get(digito=digito)
                detalle_opcion[0] = opcion
            except Opcion.DoesNotExist:
                detalle_opcion[0] = digito
        return detalle_opciones

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
        porcentaje_atendidos = (100.0 * float(total_atentidos) /
            float(total_contactos))

        total_no_atendidos = dic_totales['total_no_atendidos']
        porcentaje_no_atendidos = (100.0 * float(total_no_atendidos) /
            float(total_contactos))

        total_no_llamados = dic_totales['total_no_llamados']
        porcentaje_no_llamados = (100.0 * float(total_no_llamados) /
            float(total_contactos))

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
                opcion_x_porcentaje[opcion] = (100.0 * float(cantidad_opcion) /
                    float(dic_totales['total_opciones']))
                if not opcion in opciones_campana:
                    opcion_invalida_x_cantidad[opcion] = cantidad_opcion
                    opcion_invalida_x_porcentaje[opcion] = (100.0 *
                        float(cantidad_opcion) /
                        float(dic_totales['total_opciones']))
                else:
                    opcion_valida_x_cantidad[opcion] = cantidad_opcion
                    opcion_valida_x_porcentaje[opcion] = (100.0 *
                        float(cantidad_opcion) /
                        float(dic_totales['total_opciones']))

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

    def crea_reporte_csv(self):
        from fts_daemon.models import EventoDeContacto

        assert self.estado == Campana.ESTADO_FINALIZADA

        dirname = 'reporte_campana'
        filename = "{0}-reporte.csv".format(self.id)
        file_path = "{0}/{1}/{2}".format(settings.MEDIA_ROOT, dirname,
                                         filename)
        file_url = "{0}{1}/{2}".format(settings.MEDIA_URL, dirname, filename)
        if os.path.exists(file_path):
            # Esto no debería suceder.
            logger.error("crea_reporte_csv(): Ya existe archivo CSV de "
                         "descarga para la campana %s", self.pk)
            assert not os.path.exists(file_path)

        dirname, filename = crear_archivo_en_media_root(dirname,
            "{0}-reporte".format(self.id), ".csv")

        values = EventoDeContacto.objects_estadisticas\
            .obtener_opciones_por_contacto(self.pk)

        with open(file_path, 'wb') as csvfile:
            # Creamos encabezado
            encabezado = ["nro_telefono"]
            opciones_dict = dict([(op.digito, op.get_descripcion_de_opcion())
                for op in self.opciones.all()])
            for opcion in range(10):
                try:
                    encabezado.append(opciones_dict[opcion])
                except KeyError:
                    encabezado.append("#{0} - Opcion invalida".format(opcion))

            # Creamos csvwriter y guardamos encabezado y luego datos
            csvwiter = csv.writer(csvfile)
            csvwiter.writerow(encabezado)
            for telefono, lista_eventos in values:
                lista_opciones = [telefono]
                for opcion in range(10):
                    evento = EventoDeContacto.NUMERO_OPCION_MAP[opcion]
                    if evento in lista_eventos:
                        lista_opciones.append(1)
                    else:
                        lista_opciones.append(None)
                csvwiter.writerow(lista_opciones)
        return file_url

    def obtener_url_reporte_csv_descargar(self):
        assert self.estado == Campana.ESTADO_FINALIZADA

        dirname = 'reporte_campana'
        filename = "{0}-reporte.csv".format(self.id)
        file_path = "{0}/{1}/{2}".format(settings.MEDIA_ROOT, dirname,
                                         filename)
        file_url = "{0}{1}/{2}".format(settings.MEDIA_URL, dirname,
                                        filename)
        if os.path.exists(file_path):
            return file_url

        # Esto no debería suceder.
        logger.error("obtener_url_reporte_csv_descargar(): NO existe archivo"
                     " CSV de descarga para la campana %s", self.pk)
        assert os.path.exists(file_path)

    def valida_actuaciones(self):
        """
        Este método verifica que la actuaciones de una campana, sean válidas.
        Corrobora que al menos uno de los días semanales del rango de fechas
        de la campana concuerde con algún dia de la actuación que tenga la
        campana al momento de ser consultado este método.
        Si la campaña tiene un solo día de ejecución o si tiene un solo día
        de actuación, y los días semanales coinciden y es hoy, valida que
        hora actual sea menor que la hora_hasta de la actuación.
        """
        valida = False
        hoy_ahora = datetime.datetime.today()
        hoy = hoy_ahora.date()
        ahora = hoy_ahora.time()

        fecha_inicio = self.fecha_inicio
        fecha_fin = self.fecha_fin

        lista_actuaciones = [actuacion.dia_semanal for actuacion in
                             self.actuaciones.all()]

        dias_totales = (self.fecha_fin - self.fecha_inicio).days + 1
        for numero_dia in range(dias_totales):
            dia_actual = (self.fecha_inicio + datetime.timedelta(
                days=numero_dia))
            dia_semanal_actual = dia_actual.weekday()

            if dia_semanal_actual in lista_actuaciones:
                valida = True
                actuaciones_diaria = self.actuaciones.filter(
                    dia_semanal=dia_semanal_actual)
                for actuacion in actuaciones_diaria:
                    if dia_actual == hoy and ahora > actuacion.hora_hasta:
                        valida = False
        return valida

    def obtener_actuaciones_validas(self):
        hoy_ahora = datetime.datetime.today()
        hoy = hoy_ahora.date()
        ahora = hoy_ahora.time()

        fecha_inicio = self.fecha_inicio
        fecha_fin = self.fecha_fin

        lista_actuaciones = [actuacion.dia_semanal for actuacion in
                             self.actuaciones.all()]
        lista_actuaciones_validas = []

        dias_totales = (self.fecha_fin - self.fecha_inicio).days + 1
        for numero_dia in range(dias_totales):
            dia_actual = (self.fecha_inicio + datetime.timedelta(
                days=numero_dia))
            dia_semanal_actual = dia_actual.weekday()

            if dia_semanal_actual in lista_actuaciones:
                actuaciones_diaria = self.actuaciones.filter(
                    dia_semanal=dia_semanal_actual)
                for actuacion in actuaciones_diaria:
                    actuacion_valida = True
                    if dia_actual == hoy and ahora > actuacion.hora_hasta:
                        actuacion_valida = False

                    if actuacion_valida:
                        lista_actuaciones_validas.append(actuacion)
        return lista_actuaciones_validas

    def procesar_finalizada(self):
        """
        Este método se encarga de invocar los pasos necesarios en el proceso
        de deuración de eventos de contactos de la campaña.
        """
        assert (self.estado == Campana.ESTADO_FINALIZADA,
                "Solo se depuran  campanas finalizadas")

        # Se calculan por última vez las estadisticas, haciendo que se genere
        # el proceso de agregación de eventos de contactos por última vez.
        self.calcular_estadisticas(
            AgregacionDeEventoDeContacto.TIPO_AGREGACION_DEPURACION)

        # Se crea el reporte csv para que esté disponible para su descara.
        self.crea_reporte_csv()

        # Invoca al método de EventoDeContacto encargado de procesar la
        # depuración en si.
        from fts_daemon.models import EventoDeContacto
        EventoDeContacto.objects.depurar_eventos_de_contacto(self.pk)

    def obtener_contactos_pendientes(self):
        """
        Este método se encarga de devolver los contactos que no tengan el
        evento originate generado, o sea, que están pendientes.
        """
        from fts_daemon.models import EventoDeContacto

        assert (self.estado == Campana.ESTADO_FINALIZADA,
                "Solo se aplica la búsqueda a campanas finalizadas")

        cursor = connection.cursor()
        sql = """SELECT telefono, array_agg(evento)
            FROM fts_web_contacto INNER JOIN %s
            ON fts_web_contacto.id = %s.contacto_id
            WHERE campana_id = %s
            GROUP BY contacto_id, telefono
            HAVING not( %s = ANY(array_agg(evento)))
        """

        nombre_tabla = "EDC_depurados_{0}".format(self.pk)
        params = [nombre_tabla, self.pk,
                  EventoDeContacto.EVENTO_DAEMON_ORIGINATE_SUCCESSFUL]

        with log_timing(logger,
                        "obtener_contactos_pendientes() tardo %s seg"):
            cursor.execute(sql, params)
            # FIXME: fetchall levanta todos los datos en memoria. Ver FTS-197.
            values = cursor.fetchall()

        return values

    def __unicode__(self):
        return self.nombre

    def get_nombre_contexto_para_asterisk(self):
        """Devuelve un texto para ser usado en Asterisk,
        para nombrar el contexto asociado a la campana.
        """
        assert self.id
        return 'campania_{0}'.format(self.id)

    def clean(self, *args, **kwargs):
        """
        Valida que al crear una campaña la fechas de
        inicialización sea menor o igual a la fecha de
        finalización.
        """
        super(Campana, self).clean(*args, **kwargs)

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

        try:
            cantidad_contactos = self.bd_contacto.get_cantidad_contactos()
        except:
            pass
        else:
            if not self.cantidad_canales < cantidad_contactos:
                raise ValidationError({
                        'cantidad_canales': ["La cantidad de canales debe ser\
                            menor a la cantidad de contactos de la base de datos."]
                    })


#==============================================================================
# AgregacionDeEventoDeContacto
#==============================================================================


class AgregacionDeEventoDeContactoManager(models.Manager):
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

        if not total_contactos:
            logger.warn("procesa_agregacion(): saliendo porque la "
                "bd para la campana %s no posee datos", campana.id)
            return dic_totales

# TODO: eliminar todo este codigo
#        try:
#            ultima_agregacion_campana = self.get(campana_id=campana_id,
#                numero_intento=cantidad_intentos)
#            # Si la obtención de ultima_agregacion_campana no da excepción
#            # quiere decir que ya se generaron los registros de agregación
#            # para la campana y hay que actualizarlos desde el último
#            # evento hasta hoy y ahora.
#            try:
#                timestamp_ultimo_evento = \
#                    ultima_agregacion_campana.timestamp_ultimo_evento
#
#                assert all(agregacion.timestamp_ultimo_evento ==
#                    timestamp_ultimo_evento for agregacion in self.filter(
#                    campana_id=campana_id)),\
#                    """Los timestamp_ultimo_evento no son iguales para
#                    todos los registros de AgregacionDeEventoDeContacto
#                    para la Campana {0}.""".format(campana_id)
#                self.establece_agregacion(campana_id, cantidad_intentos,
#                    tipo_agregacion, timestamp_ultimo_evento)
#            except:
#                # FIXME: Ver solución para cuándo se desata el assert.
#                # Ocurre cuándo se actualiza (F5) el template de manera
#                # muy seguida.
#                pass
#
#        except AgregacionDeEventoDeContacto.DoesNotExist:
#            # Si la obtención de ultima_agregacion_campana da excepción
#            # quiere decir que es la primera vez que se quiere ver el
#            # Reporte o la Supervisión y no está generados los registros
#            # de agregacion para la campana. Se generan los registros sin
#            # tener en cuenta un timestamp, toma todos los eventos de
#            # EventoDeContacto para la campana.
#            self.establece_agregacion(campana_id, cantidad_intentos,
#                tipo_agregacion)

        with log_timing(logger,
            "procesa_agregacion(): recalculo de agregacion tardo %s seg"):
            with transaction.atomic():
                cursor = connection.cursor()
                cursor.execute("SELECT update_agregacion_edc_py_v1(%s)",
                    [campana.id])

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
    cantidad_intentos = models.IntegerField(default=0)
    cantidad_finalizados = models.IntegerField(default=0)
    cantidad_opcion_0 = models.IntegerField(default=0)
    cantidad_opcion_1 = models.IntegerField(default=0)
    cantidad_opcion_2 = models.IntegerField(default=0)
    cantidad_opcion_3 = models.IntegerField(default=0)
    cantidad_opcion_4 = models.IntegerField(default=0)
    cantidad_opcion_5 = models.IntegerField(default=0)
    cantidad_opcion_6 = models.IntegerField(default=0)
    cantidad_opcion_7 = models.IntegerField(default=0)
    cantidad_opcion_8 = models.IntegerField(default=0)
    cantidad_opcion_9 = models.IntegerField(default=0)
    timestamp_ultima_actualizacion = models.DateTimeField(auto_now_add=True)
    timestamp_ultimo_evento = models.DateTimeField()
    tipo_agregacion = models.IntegerField(null=True)

    def __unicode__(self):
        return "AgregacionDeEventoDeContacto-{0}-{1}".format(
            self.campana_id, self.numero_intento)


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

    def get_descripcion_de_opcion(self):
        if self.accion == Opcion.DERIVAR:
            if self.grupo_atencion:
                return "#{0} - Derivar a '{1}'".format(self.digito,
                    self.grupo_atencion.nombre)
            else:
                return "#{0} - Derivar".format(self.digito)
        if self.accion == Opcion.CALIFICAR:
            if self.calificacion:
                return "#{0} - Calificar '{1}'".format(self.digito,
                    self.calificacion.nombre)
            else:
                return "#{0} - Calificar".format(self.digito)
        if self.accion == Opcion.REPETIR:
            return "#{0} - Repetir".format(self.digito)

        return "#{0} - tipo de opcion desconocida".format(self.digito)

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
