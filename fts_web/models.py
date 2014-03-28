# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from django.db import models
from fts_web import managers


class GrupoAtencion(models.Model):
    objects = managers.GrupoAtencionManager()
    actives = managers.ActiveGrupoAtencionManager()

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
    active = models.BooleanField(
        default=True,
        editable=False,
    )

    def __unicode__(self):
        if self.active:
            return self.nombre
        return '(ELiminado) {0}'.format(self.nombre)

    def delete(self, *args, **kwargs):
        if self.active:
            self.active = False
            self.save()

    def get_ring_stratedy(self):
        ring_strategy_dic = dict(self.RING_STRATEGY_CHOICES)
        return ring_strategy_dic[self.ring_strategy]

    def get_cantidad_agentes(self):
        return self.agente_grupo_atencion.all().count()


class AgenteGrupoAtencion(models.Model):
    numero_interno = models.PositiveIntegerField(
        null=True, blank=True,
    )
    grupo_atencion = models.ForeignKey(
        'GrupoAtencion',
        related_name='agente_grupo_atencion'
    )
    active = models.BooleanField(
        default=True,
        editable=False,
    )

    def __unicode__(self):
        if self.active:
            return '{0} >> {1}'.format(
                self.grupo_atencion, self.numero_interno)
        return '(ELiminado) {0} >> {1}'.format(
                self.grupo_atencion, self.numero_interno)

    def delete(self, *args, **kwargs):
        if self.active:
            self.active = False
            self.save()


class ListaContacto(models.Model):
    nombre = models.CharField(
        max_length=128,
    )
    active = models.BooleanField(
        default=True,
        editable=False,
    )

    def __unicode__(self):
        if self.active:
            return self.nombre
        return '(ELiminado) {0}'.format(self.nombre)


class Contacto(models.Model):
    telefono = models.PositiveIntegerField()
    datos = models.TextField(
        blank=True, null=True,
    )
    lista_contacto = models.ForeignKey(
        'ListaContacto',
        related_name='contacto'
    )
    active = models.BooleanField(
        default=True,
        editable=False,
    )

    def __unicode__(self):
        if self.active:
            return '{0} >> {1}'.format(
                self.lista_contacto, self.telefono)
        return '(ELiminado) {0}'.format(self.telefono)


class Campana(models.Model):
    """Una campaña del call center"""
    ESTADO_EN_DEFINICION = 1
    ESTADO_ACTIVA = 2
    ESTADO_PAUSADA = 3
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

    bd_contacto = models.ForeignKey(
        'ListaContacto',
        related_name='campanas'
    )

    def __unicode__(self):
        return self.nombre
