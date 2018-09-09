# -*- coding: utf-8 -*-
# Copyright (C) 2018 Freetech Solutions

# This file is part of OMniLeads

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program.  If not, see http://www.gnu.org/licenses/.
#

"""Aca se encuentran las vistas para agregar los agente a la campañas/cola
por la relacion esta en cola ya que se hizo con un modelo de queue sacado de la
documentacion de asterisk"""

from __future__ import unicode_literals


from django.contrib import messages
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect
from django.views.generic import FormView, TemplateView
from ominicontacto_app.forms import QueueMemberForm, GrupoAgenteForm
from ominicontacto_app.models import Campana, QueueMember, Grupo, AgenteProfile
from ominicontacto_app.services.creacion_queue import (ActivacionQueueService,
                                                       RestablecerDialplanError)
from ominicontacto_app.utiles import elimina_espacios
from ominicontacto_app.services.asterisk_ami_http import AsteriskHttpClient,\
    AsteriskHttpQueueRemoveError


import logging as logging_

logger = logging_.getLogger(__name__)


class QueueMemberCreateView(FormView):
    """Vista para agregar un agente a una campana"""
    model = QueueMember
    form_class = QueueMemberForm
    template_name = 'queue/queue_member.html'

    def get_form(self):
        self.form_class = self.get_form_class()
        # agentes = AgenteProfile.objects.filter(reported_by=self.request.user)
        agentes = AgenteProfile.objects.filter(is_inactive=False)
        return self.form_class(members=agentes, **self.get_form_kwargs())

    def form_valid(self, form):
        campana = Campana.objects.get(pk=self.kwargs['pk_campana'])
        self.object = form.save(commit=False)
        # valido que este agente no se encuentre agregado en esta campana
        existe_member = QueueMember.objects.\
            existe_member_queue(self.object.member, campana.queue_campana)

        if existe_member:
            message = 'Operación Errónea! \
                Este miembro ya se encuentra en esta cola'
            messages.add_message(
                self.request,
                messages.ERROR,
                message,
            )
            return self.form_invalid(form)
        else:
            self.object.queue_name = campana.queue_campana
            self.object.id_campana = "{0}_{1}".format(campana.id,
                                                      elimina_espacios(campana.nombre))
            self.object.membername = self.object.member.user.get_full_name()
            self.object.interface = """Local/{0}@from-queue/n""".format(
                self.object.member.sip_extension)
            self.object.paused = 0  # por ahora no lo definimos
            self.object.save()

        return super(QueueMemberCreateView, self).form_valid(form)

    def form_invalid(self, form):
        return self.render_to_response(
            self.get_context_data(queue_member_form=form))

    def get_context_data(self, **kwargs):
        context = super(
            QueueMemberCreateView, self).get_context_data(**kwargs)
        campana = Campana.objects.get(pk=self.kwargs['pk_campana'])
        grupo_agente_form = GrupoAgenteForm(self.request.GET or None)
        context['grupo_agente_form'] = grupo_agente_form

        context['campana'] = campana
        if campana.type is Campana.TYPE_ENTRANTE:
            context['url_finalizar'] = 'campana_list'
        elif campana.type is Campana.TYPE_DIALER:
            context['url_finalizar'] = 'campana_dialer_list'
        elif campana.type is Campana.TYPE_MANUAL:
            context['url_finalizar'] = 'campana_manual_list'
        elif campana.type is Campana.TYPE_PREVIEW:
            context['url_finalizar'] = 'campana_preview_list'
        return context

    def get_success_url(self):
        return reverse(
            'queue_member_campana',
            kwargs={"pk_campana": self.kwargs['pk_campana']})


class GrupoAgenteCreateView(FormView):
    """Vista para agregar grupo de agentes a una campana"""
    model = QueueMember
    form_class = GrupoAgenteForm
    template_name = 'queue/queue_member.html'

    def form_valid(self, form):
        campana = Campana.objects.get(pk=self.kwargs['pk_campana'])
        grupo_id = form.cleaned_data.get('grupo')
        grupo = Grupo.objects.get(pk=grupo_id)
        # agentes = grupo.agentes.filter(reported_by=self.request.user)
        agentes = grupo.agentes.filter(is_inactive=False)
        # agrega los agentes a la campana siempre cuando no se encuentren agregados
        for agente in agentes:
            QueueMember.objects.get_or_create(
                member=agente,
                queue_name=campana.queue_campana,
                defaults={'membername': agente.user.get_full_name(),
                          'interface': """Local/{0}@from-queue/n""".format(
                              agente.sip_extension),
                          'penalty': 0,
                          'paused': 0,
                          'id_campana': "{0}_{1}".format(
                              campana.id, elimina_espacios(campana.nombre))},
            )
        return super(GrupoAgenteCreateView, self).form_valid(form)

    def get_context_data(self, **kwargs):
        context = super(
            GrupoAgenteCreateView, self).get_context_data(**kwargs)
        campana = Campana.objects.get(pk=self.kwargs['pk_campana'])
        context['campana'] = campana
        if campana.type is Campana.TYPE_ENTRANTE:
            context['url_finalizar'] = 'campana_list'
        elif campana.type is Campana.TYPE_DIALER:
            context['url_finalizar'] = 'campana_dialer_list'
        elif campana.type is Campana.TYPE_MANUAL:
            context['url_finalizar'] = 'campana_manual_list'
        elif campana.type is Campana.TYPE_PREVIEW:
            context['url_finalizar'] = 'campana_preview_list'
        return context

    def get_success_url(self):
        return reverse(
            'queue_member_campana',
            kwargs={"pk_campana": self.kwargs['pk_campana']})


class QueueMemberCampanaView(TemplateView):
    """Vista template despliega el template de cual se van agregar agente o grupos de
    agentes a la campana"""
    template_name = 'queue/queue_member.html'

    def get_object(self, queryset=None):
        campana = Campana.objects.get(pk=self.kwargs['pk_campana'])
        return campana.queue_campana

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        activacion_queue_service = ActivacionQueueService()
        try:
            activacion_queue_service.activar()
        except RestablecerDialplanError, e:
            message = ("<strong>Operación Errónea!</strong> "
                       "No se pudo confirmar la creación del dialplan  "
                       "al siguiente error: {0}".format(e))
            messages.add_message(
                self.request,
                messages.ERROR,
                message,
            )

        # agentes = AgenteProfile.objects.filter(reported_by=request.user)
        agentes = AgenteProfile.objects.filter(is_inactive=False)
        queue_member_form = QueueMemberForm(data=self.request.GET or None,
                                            members=agentes)
        grupo_agente_form = GrupoAgenteForm(self.request.GET or None)
        context = self.get_context_data(**kwargs)
        context['queue_member_form'] = queue_member_form
        context['grupo_agente_form'] = grupo_agente_form
        return self.render_to_response(context)

    def get_context_data(self, **kwargs):
        context = super(
            QueueMemberCampanaView, self).get_context_data(**kwargs)
        campana = Campana.objects.get(pk=self.kwargs['pk_campana'])
        context['campana'] = campana
        if campana.type is Campana.TYPE_ENTRANTE:
            context['url_finalizar'] = 'campana_list'
        elif campana.type is Campana.TYPE_DIALER:
            context['url_finalizar'] = 'campana_dialer_list'
        elif campana.type is Campana.TYPE_MANUAL:
            context['url_finalizar'] = 'campana_manual_list'
        elif campana.type is Campana.TYPE_PREVIEW:
            context['url_finalizar'] = 'campana_preview_list'
        return context


def queue_member_delete_view(request, pk_queuemember, pk_campana):
    """Elimina agente asignado en la campana"""
    queue_member = QueueMember.objects.get(pk=pk_queuemember)
    agente = queue_member.member
    queue_member.delete()
    campana = Campana.objects.get(pk=pk_campana)
    # ahora vamos a remover el agente de la cola de asterisk

    queue = "{0}_{1}".format(campana.id, elimina_espacios(campana.nombre))
    interface = "SIP/{0}".format(agente.sip_extension)

    try:
        client = AsteriskHttpClient()
        client.login()
        client.queue_remove(queue, interface)

    except AsteriskHttpQueueRemoveError:
        logger.exception("QueueRemove failed - agente: %s de la campana: %s ", agente,
                         campana)

    return HttpResponseRedirect(
        reverse('queue_member_campana',
                kwargs={"pk_campana": pk_campana}
                )
    )
