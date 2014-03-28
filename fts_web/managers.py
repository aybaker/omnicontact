# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from django.db import models


class GrupoAtencionManager(models.Manager):
    """Manager para el modelo GrupoAtencion"""

    def get_queryset(self):
        """
        Sobreescribe metodo `get_queryset()`, para que todos los queries que
        se hagan, automáticamente ignorer G.A. borrados
        """
        return super(GrupoAtencionManager, self).get_query_set().filter(
            active=True)
