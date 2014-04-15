# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import logging

from django.db import models
from django.core.exceptions import ValidationError

from fts_daemon.asterisk_ami import ORIGINATE_RESULT_UNKNOWN,\
    ORIGINATE_RESULT_SUCCESS, ORIGINATE_RESULT_FAILED,\
    ORIGINATE_RESULT_CONNECT_FAILED
import os
import uuid
import re


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

    """Texto a usar en configuracion de Asterisk"""
    RING_STRATEGY_PARA_ASTERISK = dict([
        (RINGALL, 'ringall'),
        (RRMEMORY, 'rrmemory'),
    ])

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


#===============================================================================
# Base Datos Contactos
#===============================================================================

class BaseDatosContactoManager(models.Manager):
    """Manager para BaseDatosContacto"""

    def obtener_definidas(self):
        """
        Este método filtra lo objetos BaseDatosContacto que
        esté definidos.
        """
        return self.filter(sin_definir=False)


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
        #TODO: Definir path para los archivos.
        upload_to='base_datos/%Y/%m/%d',
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


#===============================================================================
# Campaña
#===============================================================================

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


SUBSITUTE_REGEX = re.compile(r'[^a-z\._-]')


def upload_to_audios_asterisk(instance, filename):
    # max_length == 200 !!!
    filename = SUBSITUTE_REGEX.sub('', filename)
    return "audios_asterisk/%Y/%m/{0}-{1}".format(
        str(uuid.uuid4()), filename)[:200]


class Campana(models.Model):
    """Una campaña del call center"""
    objects = CampanaManager()

    """La campaña esta siendo definida en el wizard"""
    ESTADO_EN_DEFINICION = 1

    """La campaña esta activa, o sea, EN_CURSO o PROGRAMADA
    A nivel de modelos, solo queremos registrar si está ACTIVA, y no nos
    importa si esta EN_CURSO (o sea, si en este momento el daemon está
    generando llamadas asociadas a la campaña) o PROGRAMADA (si todavia no
    estamos en el rango de dias y horas en los que se deben generar
    las llamadas)
    """
    ESTADO_ACTIVA = 2

    """La capaña fue pausada"""
    ESTADO_PAUSADA = 3

    """La campaña fue finalizada, automatica o manualmente"""
    ESTADO_FINALIZADA = 4

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
    fecha_inicio = models.DateTimeField()
    fecha_fin = models.DateTimeField()
    # TODO: renombrar a audio_original
    # TODO: ajustar max_length
    # TODO: evaluar de crear callable para `upload_to`
    reproduccion = models.FileField(
        #TODO: Definir path para los archivos.
        upload_to='campana/%Y/%m/%d',
    )
    #    audio_asterisk = models.FileField(
    #        upload_to=upload_to_audios_asterisk,
    #        max_length=200,
    #        null=True, blankT=True,
    #    )

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
        """Setea la campaña como finalizada"""
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
        assert self.estado in [Campana.ESTADO_ACTIVA]
        return IntentoDeContacto.objects._obtener_pendientes_de_campana(
            self.id)

    def __unicode__(self):
        return self.nombre

    def clean(self):
        """
        Valida que al crear una campaña la fechas de
        inicialización sea menor o igual a la fecha de
        finalización.
        """

        if self.fecha_inicio > self.fecha_fin:
            raise ValidationError({
                'fecha_inicio': ["La fecha de inicio debe ser\
                    mayor o igual a la fecha de finalización."],
                'fecha_fin': ["La fecha de inicio debe ser\
                    mayor o igual a la fecha de finalización."],
            })


#===============================================================================
# IntentoDeContacto
#===============================================================================

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

    def update_resultado_si_corresponde(self, intento_id, resultado):
        """Actualiza el estado del intento, dependiendo del resultado
        del comando originate.
        """
        # FIXME: falta implementar tests
        # TODO: quiza haria falta un estado 'DESCONOCIDO'
        # TODO: evaluar usar eventos en vez de cambios de estados en la BD
        #  (al estilo NoSQL)
        if resultado == ORIGINATE_RESULT_SUCCESS:
            logger.info("update_resultado_si_corresponde(): "
                "actualizando si corresponde: SUCCESS")
            # el otro lado ha atendido, actualizamos SOLO si el registro
            # no esta actualizado
            self.filter(id=intento_id,
                estado=IntentoDeContacto.ESTADO_PROGRAMADO).update(
                    estado=IntentoDeContacto.ESTADO_CONTESTO)

        elif resultado == ORIGINATE_RESULT_FAILED:
            # el comando AMI ORIGINATE fallo. No sabemos si se ha originado
            # la llamada o no.
            # ¿Que hacemos? Filtamos intentos en estado 'ESTADO_PROGRAMADO',
            # y los actualizamos. Si la llamada se ha realizado, AGI debio
            # actualizarlo a 'ATENDIO' o 'NO ATENDIO', y listo, esto no
            # habra hecho nada
            logger.info("update_resultado_si_corresponde(): "
                "actualizando si corresponde: FAILED")
            self.filter(id=intento_id,
                estado=IntentoDeContacto.ESTADO_PROGRAMADO).update(
                    estado=IntentoDeContacto.ESTADO_NO_CONTESTO)

        elif resultado == ORIGINATE_RESULT_CONNECT_FAILED:
            # No se pudo conectar a Asterisk
            logger.info("update_resultado_si_corresponde(): "
                "actualizando si corresponde: ESTADO_ERROR_INTERNO")
            self.filter(id=intento_id,
                estado=IntentoDeContacto.ESTADO_PROGRAMADO).update(
                    estado=IntentoDeContacto.ESTADO_ERROR_INTERNO)

        elif resultado == ORIGINATE_RESULT_UNKNOWN:
            # No sabemos que paso con el comando AGI...
            # Actualizamos SOLO si no está actualizado...
            logger.info("update_resultado_si_corresponde(): "
                "actualizando si corresponde: UNKNOWN")
            self.filter(id=intento_id,
                estado=IntentoDeContacto.ESTADO_PROGRAMADO).update(
                    estado=IntentoDeContacto.ESTADO_NO_CONTESTO)

        else:
            logger.error("update_resultado_si_corresponde(): "
                "resultado NO VALIDO '%s' para IntentoDeContacto %s",
                resultado, intento_id)


class IntentoDeContacto(models.Model):
    """Representa un contacto por contactar, asociado a
    una campaña. Estas instancias son actualizadas con
    cada intento, y aqui se guarda el estado final
    (ej: si se ha contactado o no)
    """

    objects = IntentoDeContactoManager()

    """EL intento esta pendiente de ser realizado"""
    ESTADO_PROGRAMADO = 1

    """El destinatario no ha atendido el llamado"""
    ESTADO_NO_CONTESTO = 2

    """El destinatario atendio el llamado"""
    ESTADO_CONTESTO = 3

    """Se produjo un error interno del sistema"""
    ESTADO_ERROR_INTERNO = 4

    ESTADO = (
        (ESTADO_PROGRAMADO, 'Pendiente'),
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
        return "Intento de campaña {} a contacto {}".format(
            self.campana.id, self.contacto.id)


#===============================================================================
# Opciones
#===============================================================================

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

    """Deriva la llamada. Ejemplo Grupo Atencion."""
    DERIVAR = 0

    """Estable una calificación a la llamada."""
    CALIFICAR = 1

    """Habilita para dejar un mensaje de voz."""
    VOICEMAIL = 2

    """Repetir el mensaje."""
    REPETIR = 3

    ACCION_CHOICES = (
        (DERIVAR, 'DERIVAR'),
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
        unique_together = ("digito", "campana")


#===============================================================================
# Actuaciones
#===============================================================================

class Actuacion(models.Model):
    """
    Representa los días de la semana y los
    horarios en que una campaña se ejecuta.
    """

    (LUNES, MARTES, MIERCOLES, JUEVES, VIERNES) = range(0, 5)
    DIA_SEMANAL_CHOICES = (
        (LUNES, 'LUNES'),
        (MARTES, 'MARTES'),
        (MIERCOLES, 'MIERCOLES'),
        (JUEVES, 'JUEVES'),
        (VIERNES, 'VIERNES'),
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
