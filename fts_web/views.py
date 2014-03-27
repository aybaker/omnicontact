# -*- coding: utf-8 -*-
from django.db.models import get_model

#from django.conf import settings
from django.contrib import messages
#from django.contrib.auth.decorators import login_required
#from django.core.files.base import ContentFile
from django.core.urlresolvers import reverse
#from django.utils.decorators import method_decorator
from django.views.generic import (
    CreateView, UpdateView)

#from fts_web.forms import (GrupoAtencionForm)

GrupoAtencion = get_model('fts_web', 'GrupoAtencion')


class GrupoAtencionCreateView(CreateView):

    template_name = 'grupo_atencion/grupo_atencion.html'
    model = GrupoAtencion
    context_object_name = 'grupo_atencion'
    #form_class = GrupoAtencionForm

    def get_context_data(self, **kwargs):
        context = super(GrupoAtencionCreateView, self).get_context_data(**kwargs)
        return context

    def get_success_url(self):
        messages.add_message(
            self.request,
            messages.SUCCESS,
            '<strong>Operación Exitosa!</strong>\
            Se llevó a cabo con éxito la creación del\
            Grupo de Atención.',
        )
        return reverse(
            'edita_grupo_atencion',
            args=(self.object.pk,))


# class GrupoAtencionUpdateView(UpdateView):

#     template_name = 'grupo_atencion/grupo_atencion.html'
#     model = GrupoAtencion
#     context_object_name = 'grupo_atencion'
#     form_class = GrupoAtencionForm

#     def get_context_data(self, **kwargs):
#         context = super(GrupoAtencionUpdateView, self).get_context_data(**kwargs)
#         return context

#     def get_success_url(self):
#         messages.add_message(
#             self.request,
#             messages.SUCCESS,
#             '<strong>Operación Exitosa!</strong>\
#             Se llevó a cabo con éxito la creación del\
#             Grupo de Atención.',
#         )
#         return reverse(
#             'edita_grupo_atencion',
#             args=(self.object.pk,))
