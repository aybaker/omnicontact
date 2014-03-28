# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db.models import get_model

from django.contrib import messages
from django.core.urlresolvers import reverse
from django.shortcuts import redirect
from django.views.generic import (
    ListView, UpdateView, DeleteView)

from fts_web.parserxls import ParserXls

from fts_web.forms import (
    GrupoAtencionForm, AgentesGrupoAtencionFormSet,
    ListaContactoForm, FileForm)

GrupoAtencion = get_model('fts_web', 'GrupoAtencion')
ListaContacto = get_model('fts_web', 'ListaContacto')
Contacto = get_model('fts_web', 'Contacto')


#===============================================================================
# Grupos de Atención
#===============================================================================


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
            kwargs={"pk": self.object.pk})


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


#===============================================================================
# Lista Contactos
#===============================================================================


class ListaContactoListView(ListView):

    template_name = 'lista_contacto/lista_listas_contacto.html'
    context_object_name = 'listas_contacto'
    model = ListaContacto

    def get_queryset(self):
        queryset = ListaContacto.objects.all()
        return queryset


class ListaContactoCreateUpdateView(UpdateView):

    template_name = 'lista_contacto/nueva_edita_listas_contacto.html'
    model = ListaContacto
    context_object_name = 'lista_contacto'
    form_class = ListaContactoForm
    form_file = FileForm

    def get_object(self, queryset=None):
        self.creating = not 'pk' in self.kwargs

        if not self.creating:
            lista_contacto = super(
                ListaContactoCreateUpdateView, self).get_object(queryset)
            return lista_contacto

    def get_context_data(self, **kwargs):
        context = super(
            ListaContactoCreateUpdateView, self).get_context_data(**kwargs)

        if 'form_file' not in context:
            context['form_file'] = self.form_file()
        return context

    def form_valid(self, form):
        return self.process_all_forms(form)

    def form_invalid(self, form):
        return self.process_all_forms(form)

    def process_all_forms(self, form):
        if form.is_valid():
            self.object = form.save()

        form_file = self.form_file(
            self.request.POST, self.request.FILES)

        is_valid = all([
            form.is_valid(),
            form_file.is_valid(),
        ])

        if is_valid:
            parserxls = ParserXls()

            file = form_file.cleaned_data['file']
            list_contactos = parserxls.read_file(file)
            for contacto in list_contactos:
                Contacto.objects.create(
                    telefono=contacto,
                    lista_contacto=self.object
                )
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
                form_file=form_file,
            )

            return self.render_to_response(context)

    def get_success_url(self):
        if self.creating:
            message = '<strong>Operación Exitosa!</strong>\
            Se llevó a cabo con éxito la creación de\
            la Base de Datos de Contactos.'
        else:
            message = '<strong>Operación Exitosa!</strong>\
            Se llevó a cabo con éxito la actualización de\
            la Base de Datos de Contactos.'

        messages.add_message(
            self.request,
            messages.SUCCESS,
            message,
        )

        return reverse(
            'edita_lista_contactos',
            kwargs={"pk": self.object.pk})
