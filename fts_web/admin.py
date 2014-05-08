# -*- coding: utf-8 -*-

"""
Customizaciones del admin de Django.
"""

from __future__ import unicode_literals

from django.contrib import admin
from fts_web import models


admin.site.register(models.GrupoAtencion)
admin.site.register(models.AgenteGrupoAtencion)

admin.site.register(models.BaseDatosContacto)
admin.site.register(models.Contacto)
admin.site.register(models.Campana)
admin.site.register(models.Opcion)
admin.site.register(models.Actuacion)
admin.site.register(models.EventoDeContacto)
