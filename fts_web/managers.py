# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from django.db import models


class GrupoAtencionManager(models.Manager):
    """Manager para el modelo GrupoAtencion"""

    def filtrar_activos(self):
        """Devuelve queryset para devolver solo los G.A activos"""
        return self.filter(active=True)
