# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from django.db import models


class GrupoAtencionManager(models.Manager):
    def filtrar_activos(self):
        return self.filter(active=True)
