# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from django.db import models


class GrupoAtencionManager(models.Manager):
    def get_query_set(self):
        return super(GrupoAtencionManager, self).get_query_set().all()


class ActiveGrupoAtencionManager(GrupoAtencionManager):
    def get_query_set(self):
        return super(ActiveGrupoAtencionManager, self).get_query_set().filter(
            active=True
        )
