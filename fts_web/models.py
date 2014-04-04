# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import logging

from django.conf import settings
from django.db import models
from fts_daemon.asterisk_ami import ORIGINATE_RESULT_UNKNOWN,\
    ORIGINATE_RESULT_SUCCESS, ORIGINATE_RESULT_FAILED


logger = logging.getLogger(__name__)


#===============================================================================
# Grupos de Atención
#===============================================================================

class GrupoAtencion(models.Model):
    """
    Representa un Grupo de Atencion, o sea, un conjunto de agentes
    a donde se puede derivar una llamada.

    Se sobreescribe el método `delete()` para implementar
    un borrado lógico.
    """

    nombre = models.CharField(
        max_length=128,
    )
    timeout = models.PositiveIntegerField()
    RINGALL, RRMEMORY = range(0, 2)
    RING_STRATEGY_CHOICES = (
        (RINGALL, 'RINGALL'),
        (RRMEMORY, 'RRMEMORY'),
    )
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

    def get_ring_strategy(self):
        return self.get_ring_strategy_display()

    def get_cantidad_agentes(self):
        return self.agentes.all().count()


class AgenteGrupoAtencion(models.Model):
    numero_interno = models.PositiveIntegerField()
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

class BaseDatosContacto(models.Model):
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
    #    active = models.BooleanField(
    #        default=True,
    #        editable=False,
    #    )

    def __unicode__(self):
        return self.nombre
        #    if self.active:
        #        return self.nombre
        #    return '(ELiminado) {0}'.format(self.nombre)

    def get_cantidad_contactos(self):
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

    def obtener_finalizadas(self):
        """
        Devuelve campañas en estado finalizadas.
        """
        return self.filter(estado=Campana.ESTADO_FINALIZADA)


class Campana(models.Model):
    """Una campaña del call center"""
    objects = CampanaManager()

    """La campaña esta siendo definida en el wizard"""
    ESTADO_EN_DEFINICION = 1

    """La campaña esta activa, o sea, EN_CURSO o PROGRAMADA
    A nivel de modelos, solo queremos registrar si está ACTIVA, y no nos
    importa si esta EN_CURSO (o sea, si en este momento el daemon está
    generando llamadas asociadas a la campaña) o PROGRAMADA (si todavia no
    estamos en el rango de dias y horas en los que se deben generar las llamadas)
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
    fecha_inicio = models.DateTimeField(
        auto_now_add=True,
    )
    fecha_fin = models.DateTimeField(
        auto_now_add=True,
    )
    reproduccion = models.FileField(
        #FIXME: Definir path para los archivos.
        upload_to='campana/%Y/%m/%d',
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
        assert self.estado in (Campana.ESTADO_EN_DEFINICION,
            Campana.ESTADO_PAUSADA)
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

    ESTADO = (
        (ESTADO_PROGRAMADO, 'Pendiente'),
        (ESTADO_NO_CONTESTO, 'No atendio'),
        (ESTADO_CONTESTO, 'Atendio'),
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
