# -*- coding: utf-8 -*-

"""
Modelos de la aplicación
"""

from __future__ import unicode_literals

from _collections import defaultdict
import datetime
import logging
import os

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import connection
from django.db import models
from fts_web.utiles import upload_to, log_timing
import pygal


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
        """

        return self.contactos.all().count()


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


upload_to_audios_asterisk = upload_to("audios_asterisk", 95)
upload_to_audios_originales = upload_to("audios_reproduccion", 95)


class Campana(models.Model):
    """Una campaña del call center"""

    objects = CampanaManager()

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
        EventoDeContacto.objects_gestion_llamadas.programar_campana(
            self.id)

    def finalizar(self):
        """
        Setea la campaña como finalizada e invoca a generarse el gráfico
        de tortas de los resultados de los intentos de contacto.
        """
        logger.info("Seteando campana %s como ESTADO_FINALIZADA", self.id)
        # TODO: esta bien generar error si el modo actual es ESTADO_FINALIZADA?
        assert self.estado in (Campana.ESTADO_ACTIVA, Campana.ESTADO_PAUSADA)
        self.estado = Campana.ESTADO_FINALIZADA
        self.save()

        try:
            self._genera_graficos_estadisticas()
        except:
            logger.exception("No se pudo generar el grafico")

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

    def url_grafico_torta(self):
        """
        Devuelve la url al gráfico svg en medias files.
        """
        path = '{0}/graficos/{1}-torta.svg'.format(settings.MEDIA_ROOT,
            self.id)
        if os.path.exists(path):
            url = '{0}graficos/{1}-torta.svg'.format(settings.MEDIA_URL,
                self.id)
            return url
        return None

    def url_grafico_torta_no_intento(self):
        """
        Devuelve la url al gráfico svg en medias files.
        """
        path = '{0}/graficos/{1}-torta-no-intento.svg'.format(
            settings.MEDIA_ROOT, self.id)
        if os.path.exists(path):
            url = '{0}graficos/{1}-torta-no-intento.svg'.format(
                settings.MEDIA_URL, self.id)
            return url
        return None

    def url_grafico_torta_opciones(self):
        """
        Devuelve la url al gráfico svg en medias files.
        """
        path = '{0}/graficos/{1}-torta-opciones.svg'.format(settings.MEDIA_ROOT,
            self.id)
        if os.path.exists(path):
            url = '{0}graficos/{1}-torta-opciones.svg'.format(
                settings.MEDIA_URL, self.id)
            return url
        return None

    def url_grafico_barra_intentos(self):
        """
        Devuelve la url al gráfico svg en medias files.
        """
        path = '{0}/graficos/{1}-barra-intentos.svg'.format(
            settings.MEDIA_ROOT, self.id)
        if os.path.exists(path):
            url = '{0}graficos/{1}-barra-intentos.svg'.format(
                settings.MEDIA_URL, self.id)
            return url
        return None

    def obtener_estadisticas(self):
        """
        Este método devuelve las estadísticas de
        la campaña actual.

        Podría procesarse esta información directamente en EventoDeContacto.
        """
        dic_estado_x_cantidad, dic_intento_x_contactos, dic_evento_x_cantidad =\
            EventoDeContacto.objects_estadisticas.\
            obtener_estadisticas_de_campana(self.id)

        total_contactos = dic_estado_x_cantidad[
            'finalizado_x_evento_finalizador'] + dic_estado_x_cantidad[
            'finalizado_x_limite_intentos'] + dic_estado_x_cantidad[
            'pendientes']

        cantidad_contestadas = dic_estado_x_cantidad[
            'finalizado_x_evento_finalizador']
        porcentaje_contestadas = float(100 * cantidad_contestadas /\
            total_contactos)

        cantidad_no_contestadas = dic_estado_x_cantidad[
            'finalizado_x_limite_intentos']
        porcentaje_no_contestadas = float(100 * cantidad_no_contestadas /\
            total_contactos)

        cantidad_pendientes = dic_estado_x_cantidad['pendientes']
        porcentaje_pendientes = float(100 * cantidad_pendientes /\
            total_contactos)

        cantidad_no_intentados = dic_estado_x_cantidad[
            'no_intentados']
        porcentaje_no_intentados = float(100 * cantidad_no_intentados /\
            total_contactos)

        #Calcula, por cada opción, la cantidad de veces seleccionada.
        opcion_x_cantidad = defaultdict(lambda: 0)
        for opcion_campana in self.opciones.all():
            evento = EventoDeContacto.NUMERO_OPCION_MAP[opcion_campana.digito]
            opcion_x_cantidad[opcion_campana.digito] +=\
                dic_evento_x_cantidad.get(evento, 0)

        #Calcula, por cada opción el porcentaje que representa.
        total_opciones = sum(opcion_x_cantidad.values())
        opcion_x_porcentaje = defaultdict(lambda: 0)
        if total_opciones:
            for opcion_campana, cantidad in opcion_x_cantidad.items():
                opcion_x_porcentaje[opcion_campana] += float(100 * cantidad /\
                total_opciones)

        #TODO: Falta calcular las opciones inválidas.
        #import pdb; pdb.set_trace()

        return {
            #Estadisticas Generales.
            'total_contactos': total_contactos,

            'cantidad_contestadas': cantidad_contestadas,
            'porcentaje_contestadas': porcentaje_contestadas,

            'cantidad_no_contestadas': cantidad_no_contestadas,
            'porcentaje_no_contestadas': porcentaje_no_contestadas,

            'cantidad_pendientes': cantidad_pendientes,
            'porcentaje_pendientes': porcentaje_pendientes,

            'cantidad_no_intentados': cantidad_no_intentados,
            'porcentaje_no_intentados': porcentaje_no_intentados,

            'dic_intento_x_contactos': dict(dic_intento_x_contactos),

            #Estadisticas de las llamadas Contestadas.
            'opcion_x_cantidad': dict(opcion_x_cantidad),
            'opcion_x_porcentaje': dict(opcion_x_porcentaje),
        }

    def _genera_graficos_estadisticas(self):
        """
        Genera el gráfico torta de los intentos de contacto de la
        campaña finalizada.
        """

        #Obtiene estadística.
        estadisticas = self.obtener_estadisticas()

        if estadisticas['total_contactos'] > 0:
            logger.info("Generando grafico para campana %s", self.id)

            path_torta = '{0}/graficos/{1}-torta.svg'.format(
                settings.MEDIA_ROOT, self.id)
            path_torta_no_intentados = '{0}/graficos/{1}-torta-no-intento.svg'\
                .format(settings.MEDIA_ROOT, self.id)
            path_torta_opciones = '{0}/graficos/{1}-torta-opciones.svg'.format(
                settings.MEDIA_ROOT, self.id)
            path_barra_contactos_x_intentos =\
                '{0}/graficos/{1}-barra-intentos.svg'.format(
                settings.MEDIA_ROOT, self.id)

            graficos_dir = '{0}/graficos/'.format(settings.MEDIA_ROOT)
            if not os.path.exists(graficos_dir):
                try:
                    os.mkdir(graficos_dir, 0755)
                except OSError:
                    logger.warn("Error al intentar crear directorio para "
                        "graficos: %s (se ignorara el error)", graficos_dir)

            #Torta: porcentajes de contestados, no contestados y pendientes.
            pie_chart = pygal.Pie()  # @UndefinedVariable
            pie_chart.title = 'Porcentajes Generales'
            pie_chart.add('Contestados', estadisticas['porcentaje_contestadas'])
            pie_chart.add('No Contestados', estadisticas[
                'porcentaje_no_contestadas'])
            pie_chart.add('Pendientes', estadisticas['porcentaje_pendientes'])
            pie_chart.render_to_file(path_torta)

            #Torta: porcentajes de Contactos No llamados.
            con_intentos = 100 - estadisticas['porcentaje_no_intentados']
            pie_chart = pygal.Pie()  # @UndefinedVariable
            pie_chart.title = 'Porcentaje Contactos sin intento de llamada'
            pie_chart.add('Con Intento', con_intentos)
            pie_chart.add('Sin Intento', estadisticas[
                'porcentaje_no_intentados'])
            pie_chart.render_to_file(path_torta_no_intentados)

            #Torta: porcentajes de opciones selecionadas.
            dic_opcion_x_porcentaje = estadisticas['opcion_x_porcentaje']
            pie_chart = pygal.Pie()  # @UndefinedVariable
            pie_chart.title = 'Porcentajes Opciones'
            for opcion, porcentaje in dic_opcion_x_porcentaje.items():
                pie_chart.add('#{0}'.format(opcion), porcentaje)
            pie_chart.render_to_file(path_torta_opciones)

            #Barra: intentos x cantidad contactos.
            dic_intento_x_contactos = estadisticas['dic_intento_x_contactos']
            intentos = [dic_intento_x_contactos[intentos] for intentos, _ in\
                dic_intento_x_contactos.items()]
            line_chart = pygal.Bar(show_legend=False)  # @UndefinedVariable
            line_chart.title = 'Cantidad de Contactos por Número de Intentos.'
            line_chart.x_labels = map(str, range(0,
                len(dic_intento_x_contactos)))
            line_chart.add('Cantidad', intentos)
            line_chart.render_to_file(path_barra_contactos_x_intentos)
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
# EventoDeContacto
#==============================================================================

class EventoDeContactoManager(models.Manager):
    """Manager para EventoDeContacto"""

    def inicia_intento(self,
        campana_id, contacto_id):
        """Crea evento EVENTO_DAEMON_INICIA_INTENTO"""
        return self.create(campana_id=campana_id,
            contacto_id=contacto_id,
            evento=EventoDeContacto.EVENTO_DAEMON_INICIA_INTENTO)

    def create_evento_daemon_originate_successful(self,
        campana_id, contacto_id):
        """Crea evento EVENTO_DAEMON_ORIGINATE_SUCCESSFUL"""
        return self.create(campana_id=campana_id,
            contacto_id=contacto_id,
            evento=EventoDeContacto.\
                EVENTO_DAEMON_ORIGINATE_SUCCESSFUL)

    def create_evento_daemon_originate_failed(self,
        campana_id, contacto_id):
        """Crea evento EVENTO_DAEMON_ORIGINATE_FAILED"""
        return self.create(campana_id=campana_id,
            contacto_id=contacto_id,
            evento=EventoDeContacto.\
                EVENTO_DAEMON_ORIGINATE_FAILED)

    def create_evento_daemon_originate_internal_error(self,
        campana_id, contacto_id):
        """Crea evento
        EventoDeContacto.EVENTO_DAEMON_ORIGINATE_INTERNAL_ERROR"""
        return self.create(campana_id=campana_id,
            contacto_id=contacto_id,
            evento=EventoDeContacto.\
                EVENTO_DAEMON_ORIGINATE_INTERNAL_ERROR)

    def dialplan_local_channel_pre_dial(self, campana_id, contacto_id):
        """Crea evento
        EventoDeContacto.EVENTO_ASTERISK_DIALPLAN_LOCAL_CHANNEL_INICIADO
        """
        return self.create(campana_id=campana_id,
            contacto_id=contacto_id,
            evento=EventoDeContacto.\
                EVENTO_ASTERISK_DIALPLAN_LOCAL_CHANNEL_INICIADO)

    def dialplan_local_channel_post_dial(self, campana_id, contacto_id, ev):
        """Crea evento asociado a resultado de Dial() / DIALSTATUS"""
        if not ev in EventoDeContacto.DIALSTATUS_MAP.keys():
            logger.warn("dialplan_local_channel_post_dial(): se recibio "
                "evento que no es parte de DIALSTATUS_MAP: %s", ev)
        return self.create(campana_id=campana_id,
            contacto_id=contacto_id,
            evento=ev)

    def dialplan_campana_iniciado(self, campana_id, contacto_id):
        """Crea evento
        EventoDeContacto.EVENTO_ASTERISK_DIALPLAN_CAMPANA_INICIADO
        """
        return self.create(campana_id=campana_id,
            contacto_id=contacto_id,
            evento=EventoDeContacto.EVENTO_ASTERISK_DIALPLAN_CAMPANA_INICIADO)

    def dialplan_campana_finalizado(self, campana_id, contacto_id):
        """Crea evento
        EventoDeContacto.EVENTO_ASTERISK_DIALPLAN_CAMPANA_FINALIZADO
        """
        return self.create(campana_id=campana_id,
            contacto_id=contacto_id,
            evento=EventoDeContacto.\
                EVENTO_ASTERISK_DIALPLAN_CAMPANA_FINALIZADO)

    def fin_err_i(self, campana_id, contacto_id):
        """Crea evento
        EventoDeContacto.EVENTO_ASTERISK_DIALPLAN_CAMPANA_ERR_I
        """
        return self.create(campana_id=campana_id,
            contacto_id=contacto_id,
            evento=EventoDeContacto.\
                EVENTO_ASTERISK_DIALPLAN_CAMPANA_ERR_I)

    def fin_err_t(self, campana_id, contacto_id):
        """Crea evento
        EventoDeContacto.EVENTO_ASTERISK_DIALPLAN_CAMPANA_ERR_T
        """
        return self.create(campana_id=campana_id,
            contacto_id=contacto_id,
            evento=EventoDeContacto.\
                EVENTO_ASTERISK_DIALPLAN_CAMPANA_ERR_T)

    def opcion_seleccionada(self, campana_id, contacto_id, numero):
        """Crea evento
        EventoDeContacto.EVENTO_ASTERISK_OPCION_X
        """
        evento = EventoDeContacto.NUMERO_OPCION_MAP[int(numero)]
        return self.create(campana_id=campana_id,
            contacto_id=contacto_id,
            evento=evento)

    def get_eventos_finalizadores(self):
        """Devuelve eventos que permiten marcar una llamada como
        finalizada, o sea, que ya no debe ser tendia en cuenta
        al realizar futuras llamadas para la campaña.
        """
        values = []
        for name in settings.FTS_EVENTOS_FINALIZADORES:
            assert name in dir(EventoDeContacto)
            values.append(getattr(EventoDeContacto, name))
        return values

    def get_nombre_de_evento(self, evento_id):
        # TODO: cachear estas cosas pre-procesadas!
        _cached = getattr(self, '__map_nombres_de_evento', None)
        if not _cached:
            names = [const for const in dir(EventoDeContacto)
                if const.startswith("EVENTO_")]
            names = [const for const in names
                if type(getattr(EventoDeContacto, const)) == int]
            _cached = dict([(getattr(EventoDeContacto, const), const)
                for const in names])
            self.__map_nombres_de_evento = _cached
        return _cached.get(evento_id, None)


class SimuladorEventoDeContactoManager():
    """Simula acciones. Estos metodos son utilizados para pruebas,
    o simular distintas acciones, pero NO deben utilizarse
    en produccion.

    Tambien tiene metodos utilizados en scripst de pruebas
    y tests cases.
    """

    def simular_realizacion_de_intentos(self, campana_id, probabilidad=0.33):
        """
        Crea eventos EVENTO_DAEMON_INICIA_INTENTO para contactos de
        una campana.

        :param probabilidad: Para que porcentage (aprox) de los contactos hay
               que crear intentos. Para crear intentos para TODOS, usar valor
               mayor a 1.0
        :type probabilidad: float
        """
        assert settings.DEBUG or settings.FTS_TESTING_MODE
        return self.simular_evento(campana_id,
            evento=EventoDeContacto.EVENTO_DAEMON_INICIA_INTENTO,
            probabilidad=probabilidad)

    def simular_evento(self, campana_id, evento, probabilidad=0.33):
        """
        Crea evento para contactos de una campana.
        :param probabilidad: Para que porcentage (aprox) de los contactos hay
               que crear eventos. Para crear intentos para TODOS, usar valor
               mayor a 1.0
        :type probabilidad: float
        :param evento Evento a insertar
        :type evento: int
        """
        assert settings.DEBUG or settings.FTS_TESTING_MODE
        campana = Campana.objects.get(pk=campana_id)
        cursor = connection.cursor()
        # TODO: SEGURIDAD: sacar 'format()', usar api de BD
        sql = """
        INSERT INTO fts_web_eventodecontacto
            SELECT
                nextval('fts_web_eventodecontacto_id_seq') as "id",
                {campana_id} as "campana_id",
                contacto_id as "contacto_id",
                NOW() as "timestamp",
                {evento} as "evento"
            FROM
                (
                    SELECT DISTINCT contacto_id as "contacto_id"
                        FROM fts_web_eventodecontacto
                        WHERE campana_id = {campana_id}
                            AND random() <= {probabilidad}
                ) as "contacto_id"
        """.format(campana_id=campana.id,
                evento=int(evento),
                probabilidad=float(probabilidad))

        with log_timing(logger,
            "simular_realizacion_de_intentos() tardo %s seg"):
            cursor.execute(sql)

    def crear_bd_contactos_con_datos_random(self, cantidad):
        """Crea BD con muchos contactos"""
        assert settings.DEBUG or settings.FTS_TESTING_MODE
        bd_contactos = BaseDatosContacto.objects.create(
            nombre="PERF - {0} contactos".format(cantidad),
            archivo_importacion='inexistete.csv',
            nombre_archivo_importacion='inexistete.csv',
            sin_definir=False,
            columna_datos=1
        )

        cursor = connection.cursor()
        # TODO: SEGURIDAD: sacar 'format()', usar api de BD
        sql = """
            INSERT INTO fts_web_contacto
                SELECT
                    nextval('fts_web_contacto_id_seq') as "id",
                    (random()*1000000000000)::bigint::text as "telefono",
                    '' as "datos",
                    {0} as "bd_contacto_id"
                FROM
                    generate_series(1, {1})
        """.format(bd_contactos.id, cantidad)

        with log_timing(logger,
            "crear_bd_contactos_con_datos_random() tardo %s seg"):
            cursor.execute(sql)
        return bd_contactos


class EventoDeContactoEstadisticasManager():
    """Devuelve información resumida de eventos"""

    def obtener_count_intentos(self, campana_id):
        """Devuelve una lista de listas con información de intentos
        realizados, ordenados por cantidad de intentos (ej: 1, 2, etc.)

        Los elementos de la lista devuelta son listas, que contienen
        dos elementos:

        1. cantidad de intentos (1, 2, etc)
        2. count, cantidad de contactos que poseen esa cantidad
           de intentos

        Ejemplo: _((1, 721,), (2, 291,))_ 721 contactos fueron
        intentados 1 vez, 291 contactos 2 veces
        """
        campana = Campana.objects.get(pk=campana_id)
        cursor = connection.cursor()
        # FIXME: PERFORMANCE: quitar sub-select
        # FIXME: SEGURIDAD: sacar 'format()', usar api de BD
        sql = """SELECT DISTINCT ev_count, count(*) FROM
            (
                SELECT count(*) AS "ev_count"
                FROM fts_web_eventodecontacto
                WHERE evento = {evento} and campana_id = {campana_id}
                GROUP BY contacto_id
            ) AS "ev_count"
            GROUP BY ev_count
            ORDER BY 1
        """.format(campana_id=campana.id,
            evento=EventoDeContacto.EVENTO_DAEMON_INICIA_INTENTO)

        with log_timing(logger, "obtener_count_intentos() "
            "tardo %s seg"):
            cursor.execute(sql)
            values = cursor.fetchall()
        return values

    def obtener_count_eventos(self, campana_id):
        """Devuelve una lista de listas con información de count de eventos
        para una campana.

        Ejemplo: _((1, 412,), (2, 874,))_ implica que hay 412 eventos
        del tipo '1', 874 eventos de tipo '2'.
        """
        campana = Campana.objects.get(pk=campana_id)
        cursor = connection.cursor()
        # FIXME: PERFORMANCE: quitar sub-select
        # FIXME: SEGURIDAD: sacar 'format()', usar api de BD
        sql = """SELECT evento, count(*)
            FROM fts_web_eventodecontacto
            WHERE campana_id = {0}
            GROUP BY evento
            ORDER BY 1
        """.format(campana.id)

        cursor.execute(sql)
        with log_timing(logger,
            "obtener_count_eventos() tardo %s seg"):
            cursor.execute(sql)
            values = cursor.fetchall()
        return values

    def obtener_array_eventos_por_contacto(self, campana_id):
        """Devuelve una lista de listas con array de eventos para
        cada contacto.

        Ejemplo: _((783474, {1,22,13}, dt1), (8754278, {1,17,}, dt2))_
        implica que hay eventos de 2 contactos (783474 y 8754278), y los
        tipos de eventos son los indicados en los arrays. `dt` es el
        datetime del ultimo evento registrado.
        """
        campana = Campana.objects.get(pk=campana_id)
        cursor = connection.cursor()
        # FIXME: PERFORMANCE: quitar sub-select
        # FIXME: SEGURIDAD: sacar 'format()', usar api de BD
        sql = """SELECT contacto_id AS "contacto_id", array_agg(evento),
                    max(timestamp)
            FROM fts_web_eventodecontacto
            WHERE campana_id = {campana_id}
            GROUP BY contacto_id;
        """.format(campana_id=campana.id)

        cursor.execute(sql)
        with log_timing(logger,
            "obtener_array_eventos_por_contacto() tardo %s seg"):
            cursor.execute(sql)
            values = cursor.fetchall()
        return values

    def obtener_estadisticas_de_campana(self, campana_id):
        """Procesa estadisticas para una campana.

        Devuelve 3 dicts con estadísticas:

        1. ``counter_x_estado``: cuantos contactos estan en los distintos
           estados (definidos más abajo)
        2. ``counter_intentos``: cuantos contactos se han intentado distinta
           cantidad de veces.
        3. ``counter_por_evento``: cuantos eventos de cada tipo fueron
           producidos por los contactos

        counter_x_estado

        - ``counter_x_estado['finalizado_x_evento_finalizador']``: cantidad de
          contactos que ya están finalizados, o sea, no se intentará
          contactarlos, porque ya posee uno de los eventos finalizadores.
          Tomamos estos casos como contactos realizados exitosamente
          (sin importar si escucharon todo el mensaje, o ha seleccionado
          o no alguna opción).
        - ``counter_x_estado['finalizado_x_limite_intentos']``: cantidad de
          contactos que ya están finalizados, o sea, no se intentará
          contactarlos, porque ya se intentó contactarlos varias veces, y
          se llegó al límite de intentos definido en la campaña.
        - ``counter_x_estado['pendientes']``: cuantos contactos quedan
          pendientes por contactar.
        - ``counter_x_estado['no_intentados']``: para cuántos contactos no
          existen intentos de contacto, o sea, nunca se intentó contactarlos.
        - ``counter_x_estado['no_selecciono_opcion']``: cuántos contactos
          fueron contactados, pero NO seleccionaron ninguna opción.

        counter_intentos

        - ``counter_intentos[0]``: para cuántos contactos no existen intentos
          de contacto, o sea, nunca se intentó contactarlos.
        - ``counter_intentos[1]``: para cuántos contactos existen 1 intento
          de contacto.
        - ``counter_intentos[n]``: para cuántos contactos existen `n` intento
          de contacto. Este valor nunca debería ser mayor al límite de
          contactos establecido en la campaña.

        counter_por_evento

        - ``counter_por_evento[5]``: cuantos eventos de tipo '5' existen
        - ``counter_por_evento[41]``: cuantos eventos de tipo '41' existen
        - ``counter_por_evento[n]``: cuantos eventos de tipo `n` existen
        """
        campana = Campana.objects.get(pk=campana_id)
        array_eventos_por_contacto = self.obtener_array_eventos_por_contacto(
            campana_id)
        finalizadores = EventoDeContacto.objects.get_eventos_finalizadores()

        # counter_finalizados ««« ELIMINAR!
        counter_x_estado = {
            'finalizado_x_evento_finalizador': 0,
            'finalizado_x_limite_intentos': 0,
            'pendientes': 0,
            'no_intentados': 0,
            'no_selecciono_opcion': 0,
        }

        counter_intentos = defaultdict(lambda: 0)
        counter_por_evento = defaultdict(lambda: 0)

        # item[0] -> contact_id / item[1] -> ARRAY / item[2] -> timestamp
        for _, array_eventos, _ in array_eventos_por_contacto:
            eventos = set(array_eventos)

            ## Chequeamos cantidad de intentos
            cant_intentos = len([ev for ev in array_eventos
                if ev == EventoDeContacto.EVENTO_DAEMON_INICIA_INTENTO])
            counter_intentos[cant_intentos] += 1

            ## Chequea finalizados y no finalizados
            finalizado = False
            for finalizador in finalizadores:
                if finalizador in eventos:
                    finalizado = True
                    break

            # TODO: unificar en iterador de más arriba
            for evento in array_eventos:
                # FIXME: aqui es un buen lugar donde ignorar eventos
                # Ej: si elige más de 1 opcion, y hace falta que solo
                #  se tenga en cuenta la 1era elegida
                # (suponiendo que 'array_eventos' esta ordenado)
                counter_por_evento[evento] += 1

            if finalizado:
                counter_x_estado['finalizado_x_evento_finalizador'] += 1
            else:
                if cant_intentos >= campana.cantidad_intentos:
                    counter_x_estado['finalizado_x_limite_intentos'] += 1
                else:
                    counter_x_estado['pendientes'] += 1

            #Calcula la cantidad de contactos que no se llegó a intentar hacer
            #la llamada. Supone que array_eventos tiene al menos el evento
            #EVENTO_CONTACTO_PROGRAMADO.
            if all(evento == EventoDeContacto.EVENTO_CONTACTO_PROGRAMADO
                for evento in array_eventos):
                counter_x_estado['no_intentados'] += 1

            #Calcula la cantidad de contactos que no seleccionaron ninguna
            #opción de la campaña.
            opciones = EventoDeContacto.NUMERO_OPCION_MAP.values()
            if not any(opcion in eventos for opcion in opciones):
                counter_x_estado['no_selecciono_opcion'] += 1

        return counter_x_estado, counter_intentos, counter_por_evento


class GestionDeLlamadasManager(models.Manager):
    """Manager para EventoDeContacto, con la funcionalidad
    que es utilizada para la gestión más basica de las llamadas.

    Incluye la funcionalidad de programar llamadas a realizar,
    buscar llamadas pendientes, etc.

    Esta funcionalidad es la más crítica del sistema, en cuestiones
    de robustez y performance. Todos estos metodos deben estar
    extensamenete probados.
    """

    def programar_campana(self, campana_id):
        """Crea eventos EVENTO_CONTACTO_PROGRAMADO para todos los contactos
        de la campana.

        Hace algo equivalente al viejo
        *IntentoDeContacto.objects.crear_intentos_para_campana()*.
        """
        programar_campana_func = getattr(self,
            settings.FTS_PROGRAMAR_CAMPANA_FUNC)
        return programar_campana_func(campana_id)

    def _programar_campana_postgresql(self, campana_id):
        campana = Campana.objects.get(pk=campana_id)
        cursor = connection.cursor()

        # FIXME: SEGURIDAD: sacar 'format()', usar api de BD
        sql = """
        INSERT INTO fts_web_eventodecontacto
            SELECT
                nextval('fts_web_eventodecontacto_id_seq') as "id",
                {campana_id} as "campana_id",
                fts_web_contacto.id as "contacto_id",
                NOW() as "timestamp",
                {evento} as "evento"
            FROM
                fts_web_contacto
            WHERE
                bd_contacto_id = {bd_contacto_id}
        """.format(campana_id=campana.id,
            bd_contacto_id=campana.bd_contacto.id,
            evento=EventoDeContacto.EVENTO_CONTACTO_PROGRAMADO)

        with log_timing(logger, "_programar_campana_postgresql() "
            "tardo %s seg"):
            cursor.execute(sql)

    def _programar_campana_sqlite(self, campana_id):
        campana = Campana.objects.get(pk=campana_id)
        for contacto in campana.bd_contacto.contactos.all():
            EventoDeContacto.objects.create(
                campana_id=campana.id,
                contacto_id=contacto.id,
                evento=EventoDeContacto.EVENTO_CONTACTO_PROGRAMADO,
            )

    def obtener_pendientes(self, campana_id, limit=100):
        """Devuelve lista de listas. Cada elemento de la lista contiene
        una lista, con 2 items:
        - item[0]: cantidad de veces intentado
        - item[1]: id_contacto

        Cuando todos los pendientes han sido finalizados, devuelve
        una lista vacia.
        """
        campana = Campana.objects.get(pk=campana_id)

        finalizadores = ",".join([str(int(x))
            for x in EventoDeContacto.objects.get_eventos_finalizadores()])

        # FIXME: SEGURIDAD: sacar 'format()', usar api de BD
        sql = """
        SELECT count(*) AS "ev_count", contacto_id AS "contacto_id"
        FROM fts_web_eventodecontacto
        WHERE (evento = {ev_programado} OR evento = {ev_intento})
            AND campana_id = {campana_id}
            AND contacto_id NOT IN
            (
                SELECT DISTINCT tmp.contacto_id
                FROM fts_web_eventodecontacto AS tmp
                WHERE tmp.campana_id = {campana_id} AND
                    tmp.evento IN ({lista_eventos_finalizadores})
            )
        GROUP BY contacto_id
        HAVING count(*) < {max_intentos} + 1
        ORDER BY 1
        LIMIT {limit}
        """.format(campana_id=campana.id,
            max_intentos=campana.cantidad_intentos,
            ev_programado=EventoDeContacto.EVENTO_CONTACTO_PROGRAMADO,
            ev_intento=EventoDeContacto.EVENTO_DAEMON_INICIA_INTENTO,
            limit=int(limit),
            lista_eventos_finalizadores=finalizadores
        )

        cursor = connection.cursor()
        with log_timing(logger,
            "_obtener_pendientes() tardo %s seg"):
            cursor.execute(sql)
            values = cursor.fetchall()

        values = [(row[0] - 1, row[1],) for row in values]
        return values

    def obtener_datos_de_contactos(self, id_contactos):
        """Devuelve los datos necesarios para generar llamadas
        para los contactos pasados por parametros (lista de IDs).
        """
        if len(id_contactos) > 100:
            logger.warn("obtener_datos_de_contactos(): de id_contactos "
                "contiene muchos elementos, exactamente %s", len(id_contactos))
        with log_timing(logger, "obtener_datos_de_contactos() tardo %s seg"):
            # forzamos query
            values = list(Contacto.objects.filter(
                id__in=id_contactos).values_list('id', 'telefono'))

        return values


class EventoDeContacto(models.Model):
    """
    - http://www.voip-info.org/wiki/view/Asterisk+cmd+Dial
    - http://www.voip-info.org/wiki/view/Asterisk+variable+DIALSTATUS
    """

    objects = EventoDeContactoManager()
    objects_gestion_llamadas = GestionDeLlamadasManager()
    objects_simulacion = SimuladorEventoDeContactoManager()
    objects_estadisticas = EventoDeContactoEstadisticasManager()

    EVENTO_CONTACTO_PROGRAMADO = 1
    """El contacto asociado al evento ha sido programado, o sea,
    eventualmente se generará una llamada al contacto en cuestión.

    Todos los contactos que sólo poseen un evento de este tipo
    son contactos que nunca fueron procesados por el daemon, ni una vez.

    *Este evento es registrado por el daemon que realiza las llamadas.*
    """

    EVENTO_DAEMON_INICIA_INTENTO = 2
    """EL intento ha sido tomado por Daemon para ser procesado.
    Este evento *NO* implica que se haya realizado la llamada, pero
    *SI* que se ha tomado el contacto (asociado a este eveto)
    para intentar ser procesado. Representa un *INTENTO* de llamado.

    *Este evento es registrado por el daemon que realiza las llamadas.*
    """

    EVENTO_DAEMON_ORIGINATE_SUCCESSFUL = 11
    """El originate se produjo exitosamente.

    *Este evento es registrado por el daemon que realiza las llamadas.*
    """

    EVENTO_DAEMON_ORIGINATE_FAILED = 12
    """El comando ORIGINATE se ejecutó, pero devolvio error.

    *Este evento es registrado por el daemon que realiza las llamadas.*
    """

    EVENTO_DAEMON_ORIGINATE_INTERNAL_ERROR = 13
    """El originate no se pudo realizar por algun problema
    interno (ej: Asterisk caido, problema de login, etc.)
    Este tipo de error implica que el ORIGINATE seguramente no
    ha llegado al Asterisk.

    *Este evento es registrado por el daemon que realiza las llamadas.*
    """

    EVENTO_ASTERISK_DIALPLAN_LOCAL_CHANNEL_INICIADO = 21
    """Este evento indica que Asterisk ha inicio del proceso de la llamada,
    en en LOCAL CHANNEL (ej: en el contexto '[FTS_local_campana_NNN]').

    *Este evento es registrado via el proxy AGI.*
    """

    EVENTO_ASTERISK_DIALPLAN_CAMPANA_INICIADO = 22
    """Asterisk delegó control al context de la campaña.
    Este evento indica que Asterisk ha inicio del proceso REAL de la llamada,
    en el contexto asociado a la campaña (ej: en el contexto '[campania_NNN]').

    Asterisk "conecta" con el contex "[campania_NNN]" cuando el destinatario
    ha atendido. Por lo tanto, la existencia de este evento asociado a una
    llamada, implica que el destinatario ha contestado.

    *Este evento es registrado via el proxy AGI.*
    """

    EVENTO_ASTERISK_DIALPLAN_CAMPANA_FINALIZADO = 23
    """Asterisk llego al final del context de la campana.

    *Este evento es registrado via el proxy AGI.*
    """

    EVENTO_ASTERISK_DIALPLAN_CAMPANA_ERR_T = 24
    """Asterisk llego al final del context de la campana,
    pero como un error (exten t).

    *Este evento es registrado via el proxy AGI.*
    """

    EVENTO_ASTERISK_DIALPLAN_CAMPANA_ERR_I = 25
    """Asterisk llego al final del context de la campana,
    pero como un error (exten i).

    *Este evento es registrado via el proxy AGI.*
    """

    EVENTO_ASTERISK_DIALSTATUS_ANSWER = 31
    """Dial() - DIALSTATUS: ANSWER"""

    EVENTO_ASTERISK_DIALSTATUS_BUSY = 32
    """Dial() - DIALSTATUS: BUSY"""

    EVENTO_ASTERISK_DIALSTATUS_NOANSWER = 33
    """Dial() - DIALSTATUS: NOANSWER"""

    EVENTO_ASTERISK_DIALSTATUS_CANCEL = 34
    """Dial() - DIALSTATUS: CANCEL"""

    EVENTO_ASTERISK_DIALSTATUS_CONGESTION = 35
    """Dial() - DIALSTATUS: CONGESTION"""

    EVENTO_ASTERISK_DIALSTATUS_CHANUNAVAIL = 36
    """Dial() - DIALSTATUS: CHANUNAVAIL"""

    EVENTO_ASTERISK_DIALSTATUS_DONTCALL = 37
    """Dial() - DIALSTATUS: DONTCALL"""

    EVENTO_ASTERISK_DIALSTATUS_TORTURE = 38
    """Dial() - DIALSTATUS: TORTURE"""

    EVENTO_ASTERISK_DIALSTATUS_INVALIDARGS = 39
    """Dial() - DIALSTATUS: INVALIDARGS"""

    EVENTO_ASTERISK_DIALSTATUS_UNKNOWN = 40
    """Dial() - El valor de DIALSTATUS recibido por el sistema
    no es ninguno de los reconocidos por el sistema
    """

    EVENTO_ASTERISK_OPCION_0 = 50
    """El usuario ha seleccionado una opción 0 utilizando utilizando
    el teclado numerico.
    """

    EVENTO_ASTERISK_OPCION_1 = 51
    """El usuario ha seleccionado una opción 1 utilizando utilizando
    el teclado numerico.
    """

    EVENTO_ASTERISK_OPCION_2 = 52
    """El usuario ha seleccionado una opción 2 utilizando utilizando
    el teclado numerico.
    """

    EVENTO_ASTERISK_OPCION_3 = 53
    """El usuario ha seleccionado una opción 3 utilizando utilizando
    el teclado numerico.
    """

    EVENTO_ASTERISK_OPCION_4 = 54
    """El usuario ha seleccionado una opción 4 utilizando utilizando
    el teclado numerico.
    """

    EVENTO_ASTERISK_OPCION_5 = 55
    """El usuario ha seleccionado una opción 5 utilizando utilizando
    el teclado numerico.
    """

    EVENTO_ASTERISK_OPCION_6 = 56
    """El usuario ha seleccionado una opción 6 utilizando utilizando
    el teclado numerico.
    """

    EVENTO_ASTERISK_OPCION_7 = 57
    """El usuario ha seleccionado una opción 7 utilizando utilizando
    el teclado numerico.
    """

    EVENTO_ASTERISK_OPCION_8 = 58
    """El usuario ha seleccionado una opción 8 utilizando utilizando
    el teclado numerico.
    """

    EVENTO_ASTERISK_OPCION_9 = 59
    """El usuario ha seleccionado una opción 9 utilizando utilizando
    el teclado numerico.
    """

    NUMERO_OPCION_MAP = {
        0: EVENTO_ASTERISK_OPCION_0,
        1: EVENTO_ASTERISK_OPCION_1,
        2: EVENTO_ASTERISK_OPCION_2,
        3: EVENTO_ASTERISK_OPCION_3,
        4: EVENTO_ASTERISK_OPCION_4,
        5: EVENTO_ASTERISK_OPCION_5,
        6: EVENTO_ASTERISK_OPCION_6,
        7: EVENTO_ASTERISK_OPCION_7,
        8: EVENTO_ASTERISK_OPCION_8,
        9: EVENTO_ASTERISK_OPCION_9,
    }
    """Mapea ENTERO (numero de opcion) a EVENTO_ASTERISK_OPCION_9"""

    DIALSTATUS_MAP = {
        'ANSWER': EVENTO_ASTERISK_DIALSTATUS_ANSWER,
        'BUSY': EVENTO_ASTERISK_DIALSTATUS_BUSY,
        'NOANSWER': EVENTO_ASTERISK_DIALSTATUS_NOANSWER,
        'CANCEL': EVENTO_ASTERISK_DIALSTATUS_CANCEL,
        'CONGESTION': EVENTO_ASTERISK_DIALSTATUS_CONGESTION,
        'CHANUNAVAIL': EVENTO_ASTERISK_DIALSTATUS_CHANUNAVAIL,
        'DONTCALL': EVENTO_ASTERISK_DIALSTATUS_DONTCALL,
        'TORTURE': EVENTO_ASTERISK_DIALSTATUS_TORTURE,
        'INVALIDARGS': EVENTO_ASTERISK_DIALSTATUS_INVALIDARGS,
    }

    campana_id = models.IntegerField(db_index=True)
    contacto_id = models.IntegerField(db_index=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    evento = models.SmallIntegerField(db_index=True)
    dato = models.SmallIntegerField(null=True)

    def __unicode__(self):
        return "EventoDeContacto-{0}-{1}".format(
            self.campana_id, self.contacto_id)


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
        dia_semanal = hoy_ahora.weekday()
        hora_actual = datetime.time(
            hoy_ahora.hour, hoy_ahora.minute, hoy_ahora.second)

        if not self.dia_semanal == dia_semanal:
            return False

        if not self.hora_desde <= hora_actual <= self.hora_hasta:
            return False

        return True

    def clean(self):
        """
        Valida que al crear una actuación a una campaña
        no exista ya una actuación en el rango horario
        especificado y en el día semanal seleccionado.
        """

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
