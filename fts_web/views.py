# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db.models import get_model

from django.contrib import messages
from django.core.urlresolvers import reverse
from django.shortcuts import redirect
from django.views.generic import (
    ListView, UpdateView, DeleteView)

from fts_web.forms import (
    GrupoAtencionForm, AgentesGrupoAtencionFormSet)

GrupoAtencion = get_model('fts_web', 'GrupoAtencion')


class GrupoAtencionListView(ListView):

    template_name = 'grupo_atencion/lista_grupo_atencion.html'
    context_object_name = 'grupos_atencion'
    model = GrupoAtencion

    def get_queryset(self):
        queryset = GrupoAtencion.actives.all()
        return queryset


class GrupoAtencionCreateUpdateView(UpdateView):

    template_name = 'grupo_atencion/grupo_atencion.html'
    model = GrupoAtencion
    context_object_name = 'grupo_atencion'
    form_class = GrupoAtencionForm
    formset_agente_grupo_atencion = AgentesGrupoAtencionFormSet

    def get_object(self, queryset=None):
        self.creating = not 'pk' in self.kwargs

        if not self.creating:
            grupo_atencion = super(
                GrupoAtencionCreateUpdateView, self).get_object(queryset)
            return grupo_atencion

    def get_context_data(self, **kwargs):
        context = super(
            GrupoAtencionCreateUpdateView, self).get_context_data(**kwargs)

        if 'formset_agente_grupo_atencion' not in context:
            context['formset_agente_grupo_atencion'] = \
            self.formset_agente_grupo_atencion(
                instance=self.object
            )
        return context

    def form_valid(self, form):
        return self.process_all_forms(form)

    def form_invalid(self, form):
        return self.process_all_forms(form)

    def process_all_forms(self, form):
        if form.is_valid():
            self.object = form.save()

        formset_agente_grupo_atencion = self.formset_agente_grupo_atencion(
            self.request.POST, instance=self.object)

        is_valid = all([
            form.is_valid(),
            formset_agente_grupo_atencion.is_valid(),
        ])

        if is_valid:
            formset_agente_grupo_atencion.save()

            return redirect(self.get_success_url())
        else:
            if form.is_valid():
                self.object.delete()
                self.object = None

            messages.add_message(
                self.request,
                messages.ERROR,
                '<strong>Operación Errónea!</strong>\
                Revise y complete todos los campos obligatorios\
                para la creación de una nuevo Grupo de Atención.',
            )
            context = self.get_context_data(
                form=form,
                formset_agente_grupo_atencion=formset_agente_grupo_atencion,
            )

            return self.render_to_response(context)

    def get_success_url(self):
        if self.creating:
            message = '<strong>Operación Exitosa!</strong>\
            Se llevó a cabo con éxito la creación del\
            Grupo de Atención.'
        else:
            message = '<strong>Operación Exitosa!</strong>\
            Se llevó a cabo con éxito la actualización del\
            Grupo de Atención.'

        messages.add_message(
            self.request,
            messages.SUCCESS,
            message,
        )

        return reverse(
            'edita_grupo_atencion',
            kwargs={"pk": self.object.id})


class GrupoAtencionDeleteView(DeleteView):

    model = GrupoAtencion
    template_name = 'grupo_atencion/elimina_grupo_atencion.html'

    def get_success_url(self):
        message = '<strong>Operación Exitosa!</strong>\
        Se llevó a cabo con éxito la eliminación del\
        Grupo de Atención.'

        messages.add_message(
            self.request,
            messages.SUCCESS,
            message,
        )

        return reverse('lista_grupo_atencion')
