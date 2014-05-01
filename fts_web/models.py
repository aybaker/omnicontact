# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import os
import logging
import datetime
import pygal

from django.conf import settings

from django.db import models
from django.core.exceptions import ValidationError

from fts_web.utiles import upload_to


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
    #    def get_queryset(self):
    #        # F-I-X-M-E: esto no romperá los modelforms? Ej: form.campana. Si la campana
    #        # que referencia el modelform esta ESTADO_EN_DEFINICION, ¿aparece en el html?
    #        # Especificamente, en el caso de Campana.estado no habria problema, pero
    #        # esta medotodologia de filtrado automatico ¿podria ser un peligro
    #        # en el "borrado logico"?
    #        return super(CampanaManager, self).exclude(estado=Campana.ESTADO_EN_DEFINICION)

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

    def verifica_estado_pausada(self, pk):
        campana = self.get(pk=pk)
        if campana.estado == Campana.ESTADO_PAUSADA:
            return True
        return False


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

        IntentoDeContacto.objects.crear_intentos_para_campana(self.id)

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

        self._genera_grafico_torta()

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

    def obtener_actuaciones_en_fecha_hora(self, hoy_ahora):
        """
        Este método devuelve las actuaciones que tiene la campaña al
        en el momento *hoy_ahora* especificado.
        Valida que la fecha del momento hoy_ahora este en el rango
        de la fecha de inicio y fin de la campaña, de lo contrario
        devuelve None.
        """
        fecha_actual = hoy_ahora.date()
        dia_semanal = hoy_ahora.weekday()

        if self.fecha_inicio <= fecha_actual <= self.fecha_fin:
            return self.actuaciones.filter(dia_semanal=dia_semanal) or None
        return None

    def obtener_rango_horario_actuacion_en_fecha_hora(self, hoy_ahora):
        """
        Este método devuelve el rango horario de la actuación en
        el momento *hoy_ahora* para la campaña actual.
        Valida que la hora del momento hoy_ahora este en el rango
        de la hora de incio y fin de la actuación, de lo contrario
        devuelve None.
        """
        #Devuelve None si no tiene actuaciones hoy y ahora.
        actuaciones_hoy_ahora = self.obtener_actuaciones_en_fecha_hora(
            hoy_ahora)
        if not actuaciones_hoy_ahora:
            return None

        #Arma lista de tuplas con los  rangos horarios de
        #las actuaciones de hoy y ahora.
        actuaciones = [(actuacion.hora_desde, actuacion.hora_hasta)
            for actuacion in actuaciones_hoy_ahora]

        #Toma la actuación por la que se está ejecutando la campaña.
        #La campaña no puede tener mas de 1 actuación en una hora determinada.
        actuacion = None
        for hora_desde, hora_hasta in actuaciones:
            hora_actual = hoy_ahora.time()
            if hora_desde <= hora_actual <= hora_hasta:
                actuacion = (hora_desde, hora_hasta)

        return actuacion

    def obtener_intentos_pendientes(self):
        """Devuelve instancias de IntentoDeContacto para los que
        haya que intentar realizar llamadas.
        Solo tiene sentido ejecutar este metodo en campanas activas.
        """
        # (a) Este metodo tambien se podria poner en IntentoDeContactoManager
        # pero me parece mas asertado implementarlo en campaña, asi se
        # pueden controlar cosas como el estado de la campaña, por ejemplo.
        # (b) Otra forma sería dejar este metodo (para poder hacer controles
        # a nivel de campaña), pero la busqueda de las instancias de
        # IntentoDeContacto hacerlo usando IntentoDeContactoManager.
        # Esta alternativa me gusta (cada modelo maneja su logica), pero
        # tengo la duda de que valga la pena hacer 2 metodos en vez de 1.
        # La ventaja es que, con esta última idea, cada modelo es
        # manejado por si mismo, algo que puede ayudar a la mantenibilidad.
        # DECISION: que cada modelo maneje su parte
        #assert self.estado in [Campana.ESTADO_ACTIVA]
        return IntentoDeContacto.objects._obtener_pendientes_de_campana(
            self.id)

    def obtener_intentos_contesto(self):
        """
        Devuelve instancias de IntentoDeContacto para los que
        haya que se contesto la llamadas.
        """
        return IntentoDeContacto.objects._obtener_contesto_de_campana(
            self.id)

    def obtener_intentos_no_contesto(self):
        """
        Devuelve instancias de IntentoDeContacto para los que
        haya que no se contesto la llamadas.
        """
        return IntentoDeContacto.objects._obtener_no_contesto_de_campana(
            self.id)

    def obtener_intentos_error_interno(self):
        """
        Devuelve instancias de IntentoDeContacto para los que
        haya que se registro un error interno en la llamadas.
        """
        return IntentoDeContacto.objects._obtener_error_interno_de_campana(
            self.id)

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

    def _genera_grafico_torta(self):
        """
        Genera el gráfico torta de los intentos de contacto de la
        campaña finalizada.
        """
        path = '{0}/graficos/{1}-torta.svg'.format(settings.MEDIA_ROOT,
            self.id)

        total_contactos = self.bd_contacto.contactos.all().count()
        if total_contactos > 0:
            logger.info("Generando grafico para campana %s", self.id)
            graficos_dir = '{0}/graficos/'.format(settings.MEDIA_ROOT)
            if not os.path.exists(graficos_dir):
                try:
                    os.mkdir(graficos_dir, 0755)
                except OSError:
                    logger.warn("Error al intentar crear directorio para "
                        "graficos: %s (se ignorara el error)", graficos_dir)

            cantidad_contesto = self.obtener_intentos_contesto().count()
            cantidad_no_contesto = self.obtener_intentos_no_contesto().count()
            cantidad_pendientes = self.obtener_intentos_pendientes().count()
            cantidad_error_interno = self.obtener_intentos_error_interno().count()

            porcentaje_contesto = float(100 * cantidad_contesto /
                total_contactos)
            porcentaje_no_contesto = float(100 * cantidad_no_contesto /
                total_contactos)
            porcentaje_pendientes = float(100 * cantidad_pendientes /
                total_contactos)
            porcentaje_error_interno = float(100 * cantidad_error_interno /
                total_contactos)

            pie_chart = pygal.Pie()  # @UndefinedVariable
            pie_chart.title = 'Intentos de Contactos para la campaña {0}'.format(
                self.nombre)
            pie_chart.add('Contestados', porcentaje_contesto)
            pie_chart.add('No Contestados', porcentaje_no_contesto)
            pie_chart.add('Pendientes', porcentaje_pendientes)
            pie_chart.add('Erróneos', porcentaje_error_interno)
            pie_chart.render_to_file(path)
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


#==============================================================================
# IntentoDeContacto
#==============================================================================

class IntentoDeContactoManager(models.Manager):
    """Manager para el modelo IntentoDeContacto"""

    def crear_intentos_para_campana(self, campana_id):
        """Crea todas las instancias de 'IntentoDeContacto'
        para la campaña especificada por parametro.
        """
        # TODO: refactorizar este metodo (ver comentario que sigue)
        # Esto de la creacion de los intentos NO sigue la idea documentada
        # en 'obtener_intentos_pendientes()'
        # Para continuar con dicha idea, este metodo deberia ser privado
        # y se deberia crear un metodo en Campana que llame a este de aca.
        # El estado y demas cuestiones de Campana se chequearian en dicha clase
        logger.info("Creando IntentoDeContacto para campana %s", campana_id)
        campana = Campana.objects.get(pk=campana_id)
        assert campana.estado == Campana.ESTADO_ACTIVA
        assert campana.bd_contacto is not None
        assert not self._obtener_pendientes_de_campana(campana_id).exists()

        for contacto in campana.bd_contacto.contactos.all():
            # TODO: esto traera problemas de performance
            self.create(contacto=contacto, campana=campana)

    def _obtener_pendientes_de_campana(self, campana_id):
        """Devuelve QuerySet con intentos pendientes de una campana, ignora
        completamente las cuestiones de la campaña, como su estado.

        Esto es parte de la API interna, y no deberia usarse directamente
        nada más que desde otros Managers.

        Para buscar intentos pendientes de una campaña, usar:
            Campana.obtener_intentos_pendientes()
        """
        return self.filter(campana=campana_id,
            estado=IntentoDeContacto.ESTADO_PROGRAMADO)

    def _obtener_no_contesto_de_campana(self, campana_id):
        """Devuelve QuerySet con intentos no contestados de una campana, ignora
        completamente las cuestiones de la campaña, como su estado.

        Esto es parte de la API interna, y no deberia usarse directamente
        nada más que desde otros Managers.

        Para buscar intentos no contestados de una campaña, usar:
            Campana.obtener_intentos_no_contestados()
        """
        return self.filter(campana=campana_id,
            estado=IntentoDeContacto.ESTADO_NO_CONTESTO)

    def _obtener_contesto_de_campana(self, campana_id):
        """Devuelve QuerySet con intentos contestados de una campana, ignora
        completamente las cuestiones de la campaña, como su estado.

        Esto es parte de la API interna, y no deberia usarse directamente
        nada más que desde otros Managers.

        Para buscar intentos no contestados de una campaña, usar:
            Campana.obtener_intentos_contestados()
        """
        return self.filter(campana=campana_id,
            estado=IntentoDeContacto.ESTADO_CONTESTO)

    def _obtener_error_interno_de_campana(self, campana_id):
        """Devuelve QuerySet con intentos erroneos de una campana, ignora
        completamente las cuestiones de la campaña, como su estado.

        Esto es parte de la API interna, y no deberia usarse directamente
        nada más que desde otros Managers.

        Para buscar intentos no contestados de una campaña, usar:
            Campana.obtener_intentos_error_interno()
        """
        return self.filter(campana=campana_id,
            estado=IntentoDeContacto.ESTADO_ERROR_INTERNO)

    def update_estado_por_originate(self, intento_id, originate_ok):
        """Actualiza el estado del intento, dependiendo del resultado
        del comando originate.
        """
        # FIXME: falta implementar tests
        # TODO: quiza haria falta un estado 'DESCONOCIDO'
        # TODO: evaluar usar eventos en vez de cambios de estados en la BD
        #  (al estilo NoSQL)
        
        if originate_ok:
            self.filter(id=intento_id,
                estado=IntentoDeContacto.ESTADO_PROGRAMADO).update(
                    estado=IntentoDeContacto.ESTADO_ORIGINATE_SUCCESSFUL)
        else:
            self.filter(id=intento_id,
                estado=IntentoDeContacto.ESTADO_PROGRAMADO).update(
                    estado=IntentoDeContacto.ESTADO_ORIGINATE_FAILED)


class IntentoDeContacto(models.Model):
    """Representa un contacto por contactar, asociado a
    una campaña. Estas instancias son actualizadas con
    cada intento, y aqui se guarda el estado final
    (ej: si se ha contactado o no)
    """

    objects = IntentoDeContactoManager()

    ESTADO_PROGRAMADO = 1
    """EL intento esta pendiente de ser realizado"""

    ESTADO_ORIGINATE_SUCCESSFUL = 2
    """El originate se produjo exitosamente"""

    ESTADO_ORIGINATE_FAILED = 3
    """El originate devolvio error"""

    ESTADO_NO_CONTESTO = 4
    """El destinatario no ha atendido el llamado"""

    ESTADO_CONTESTO = 5
    """El destinatario atendio el llamado"""

    ESTADO_ERROR_INTERNO = 5
    """Se produjo un error interno del sistema"""

    ESTADO = (
        (ESTADO_PROGRAMADO, 'Pendiente'),
        (ESTADO_ORIGINATE_SUCCESSFUL, 'Originate OK'),
        (ESTADO_ORIGINATE_FAILED, 'Originate Fallo'),
        (ESTADO_NO_CONTESTO, 'No atendio'),
        (ESTADO_CONTESTO, 'Atendio'),
        (ESTADO_ERROR_INTERNO, 'Error interno'),
    )

    contacto = models.ForeignKey(
        'Contacto',
        related_name='+'
    )
    campana = models.ForeignKey(
        'Campana',
        related_name='intentos_de_contactos'
    )
    fecha_intento = models.DateTimeField(
        null=True, blank=True
    )
    estado = models.PositiveIntegerField(
        choices=ESTADO,
        default=ESTADO_PROGRAMADO,
    )

    def registra_contesto(self):
        """Registra el resultado del intento como que el destinatario
        ha contestado
        """
        # FIXME: testear
        logger.info("Registrando IntentoDeContacto %s como ESTADO_CONTESTO",
            self.id)
        assert self.estado == IntentoDeContacto.ESTADO_PROGRAMADO
        self.estado = IntentoDeContacto.ESTADO_CONTESTO
        self.save()

    def __unicode__(self):
        return "Intento de campaña {0} a contacto {1}".format(
            self.campana, self.contacto.id)


#==============================================================================
# EventoDeContacto
#==============================================================================

class EventoDeContactoManager(models.Manager):
    """Manager para EventoDeContacto"""

    def create_evento_daemon_programado(self,
        campana_id, contacto_id):
        """Crea evento EVENTO_DAEMON_PROGRAMADO"""
        return self.create(campana_id=campana_id,
            contacto_id=contacto_id,
            evento=EventoDeContacto.EVENTO_DAEMON_PROGRAMADO)

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
        """Crea evento"""
        if not ev in EventoDeContacto.DIALSTATUS_MAP.keys():
            logger.warn("dialplan_local_channel_post_dial(): se recibio "
                "evento que no es parte de DIALSTATUS_MAP: %s", ev)
        return self.create(campana_id=campana_id,
            contacto_id=contacto_id,
            evento=ev)


class EventoDeContacto(models.Model):
    """
    - http://www.voip-info.org/wiki/view/Asterisk+cmd+Dial
    - http://www.voip-info.org/wiki/view/Asterisk+variable+DIALSTATUS
    """

    objects = EventoDeContactoManager()

    EVENTO_DAEMON_PROGRAMADO = 1
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
    """Asterisk delegó control al context (de Local channel) de la campaña.
    Este evento indica que Asterisk ha inicio del proceso REAL de la llamada,
    en el contexto asociado a la campaña (ej: en el contexto '[campania_NNN]').
    Todavia no se ha realizado el Dial() al numero del contacto.

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

    # EVENTO_ASTERISK_DIALSTATUS_CUSTOM = xxx
    # """Dial() - DIALSTATUS: evento customizado (usa `dato`)"""

    # EVENTO_CUSTOMIZADO = xxx
    # """Evento customizado"""

    #EVENTO_ASTERISK_OPCION_SELECCIONADA = xxx
    #"""Opcion seleccionada"""

    #EVENTO_ASTERISK_OPCION_SELECCIONADA
    #"""Valores de `dato` para `evento`

    DIALSTATUS_MAP = {
        'ANSWER': EventoDeContacto.EVENTO_ASTERISK_DIALSTATUS_ANSWER,
        'BUSY': EventoDeContacto.EVENTO_ASTERISK_DIALSTATUS_BUSY,
        'NOANSWER': EventoDeContacto.EVENTO_ASTERISK_DIALSTATUS_NOANSWER,
        'CANCEL': EventoDeContacto.EVENTO_ASTERISK_DIALSTATUS_CANCEL,
        'CONGESTION': EventoDeContacto.EVENTO_ASTERISK_DIALSTATUS_CONGESTION,
        'CHANUNAVAIL': EventoDeContacto.EVENTO_ASTERISK_DIALSTATUS_CHANUNAVAIL,
        'DONTCALL': EventoDeContacto.EVENTO_ASTERISK_DIALSTATUS_DONTCALL,
        'TORTURE': EventoDeContacto.EVENTO_ASTERISK_DIALSTATUS_TORTURE,
        'INVALIDARGS': EventoDeContacto.EVENTO_ASTERISK_DIALSTATUS_INVALIDARGS,
    }

    #DATO_OPCION_0 = 1
    #DATO_OPCION_1 = 2
    #DATO_OPCION_2 = 3
    #DATO_OPCION_3 = 4
    #DATO_OPCION_4 = 5
    #DATO_OPCION_5 = 6
    #DATO_OPCION_6 = 7
    #DATO_OPCION_7 = 8
    #DATO_OPCION_8 = 9
    #DATO_OPCION_9 = 10

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
