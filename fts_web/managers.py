from django.db import models


class GrupoAtencionManager(models.Manager):
    def get_query_set(self):
        return super(GrupoAtencionManager, self).get_query_set().all()


class ActiveGrupoAtencionManager(GrupoAtencionManager):
    def get_query_set(self):
        #TODO: Filtrar actives cuando se implemente.
        return super(ActiveGrupoAtencionManager, self).get_query_set().all()
