# -*- coding: utf-8 -*-
from django.db import models


class GrupoAtencion(models.Model):
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
    )

    def __unicode__(self):
        return self.nombre
