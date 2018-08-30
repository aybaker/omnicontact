# -*- coding: utf-8 -*-

"""
Esta vista se configua user y password del cual se van conectar a la api de la cuál se
conecta al servicio json configurada calificacion_cliente_externa_view() en el
modulo views_calificacion_cliente
"""

from __future__ import unicode_literals


from django.core.urlresolvers import reverse, reverse_lazy
from django.views.generic import CreateView, UpdateView, ListView, DeleteView
from django.contrib.auth.hashers import make_password
from ominicontacto_app.forms import UserApiCrmForm
from ominicontacto_app.models import UserApiCrm


import logging as logging_

logger = logging_.getLogger(__name__)


class PaswordHasherMixin(object):

    def form_valid(self, form):
        self.object = form.save(commit=False)
        password = make_password(self.object.password, salt='Fuck1ngS4lt', hasher='default')
        self.object.password = password
        self.object.save()
        return super(PaswordHasherMixin, self).form_valid(form)


class UserApiCrmCreateView(PaswordHasherMixin, CreateView):
    """Vista para crear un nuevo userapicrm"""
    model = UserApiCrm
    template_name = 'base_create_update_form.html'
    form_class = UserApiCrmForm

    def get_success_url(self):
        return reverse('user_api_crm_list')


class UserApiCrmUpdateView(PaswordHasherMixin, UpdateView):
    """Vista para modificar el userapicrm"""
    model = UserApiCrm
    template_name = 'base_create_update_form.html'
    form_class = UserApiCrmForm

    def get_success_url(self):
        return reverse('user_api_crm_list')


class UserApiCrmListView(ListView):
    """Vista para listar los userapicrm"""
    model = UserApiCrm
    template_name = 'user_api_crm_list.html'


class UserApiCrmDeleteView(DeleteView):
    """Vista para eliminar el userapicrm"""
    model = UserApiCrm
    success_url = reverse_lazy('user_api_crm_list')
    template_name = 'user_api_crm_delete.html'
