# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib import admin
from fts_web import models


admin.site.register(models.GrupoAtencion)
admin.site.register(models.AgenteGrupoAtencion)
