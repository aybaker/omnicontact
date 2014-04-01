# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from django.db import models
from django.conf import settings


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
        null=True, blank=True,
    )
    timeout = models.PositiveIntegerField(
        null=True, blank=True,
    )
    RINGALL, RRMEMORY = range(0, 2)
    RING_STRATEGY_CHOICES = (
        (RINGALL, 'RINGALL'),
        (RRMEMORY, 'RRMEMORY'),
    )
    ring_strategy = models.PositiveIntegerField(
        choices=RING_STRATEGY_CHOICES,
        default=RINGALL,
        null=True, blank=True,
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
        ring_strategy_dic = dict(self.RING_STRATEGY_CHOICES)
        return ring_strategy_dic[self.ring_strategy]

    def get_cantidad_agentes(self):
        return self.agentes.all().count()


class AgenteGrupoAtencion(models.Model):
    numero_interno = models.PositiveIntegerField(
        null=True, blank=True,
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
# Lista Contactos
#===============================================================================

class ListaContacto(models.Model):
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
    telefono = models.PositiveIntegerField()
    datos = models.TextField(
        blank=True, null=True,
    )
    lista_contacto = models.ForeignKey(
        'ListaContacto',
        related_name='contactos'
    )

    def __unicode__(self):
        return '{0} >> {1}'.format(
            self.lista_contacto, self.telefono)


#===============================================================================
# Campaña
#===============================================================================

class CampanaManager(models.Manager):
    """
    Manager para Campanas
    """
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
        blank=True, null=True,
    )

    bd_contacto = models.ForeignKey(
        'ListaContacto',
        related_name='campanas'
    )

    def activar(self):
        """
        Setea la campaña como anctiva.
        """
        self.estado = Campana.ESTADO_ACTIVA
        self.save()

    def finalizar(self):
        """Setea la campaña como finalizada"""
        # TODO: esta bien generar error si el modo actual es 'ESTADO_FINALIZADA'?
        assert self.estado in (Campana.ESTADO_ACTIVA, Campana.ESTADO_PAUSADA)
        self.estado = Campana.ESTADO_FINALIZADA
        self.save()

    def __unicode__(self):
        return self.nombre
