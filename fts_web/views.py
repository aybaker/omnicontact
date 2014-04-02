# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib import messages
from django.core.urlresolvers import reverse
from django.shortcuts import redirect
from django.views.generic import (
    CreateView, DeleteView, ListView, UpdateView)

from fts_web.parserxls import ParserXls

from fts_web.forms import (
    AgentesGrupoAtencionFormSet, CampanaForm, ConfirmaForm,
    FileForm, GrupoAtencionForm, ListaContactoForm,
)
from fts_web.models import (
    Campana, Contacto, GrupoAtencion, ListaContacto,
)


#===============================================================================
# Grupos de Atención
#===============================================================================


class GrupoAtencionListView(ListView):

    template_name = 'grupo_atencion/lista_grupo_atencion.html'
    context_object_name = 'grupos_atencion'
    model = GrupoAtencion

    #def get_queryset(self):
    #    queryset = GrupoAtencion.objects.filtrar_activos()
    #    return queryset


class GrupoAtencionMixin(object):

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


class GrupoAtencionCreateView(CreateView, GrupoAtencionMixin):

    template_name = 'grupo_atencion/grupo_atencion.html'
    model = GrupoAtencion
    context_object_name = 'grupo_atencion'
    form_class = GrupoAtencionForm
    formset_agente_grupo_atencion = AgentesGrupoAtencionFormSet

    def get_context_data(self, **kwargs):
        context = super(
            GrupoAtencionCreateView, self).get_context_data(**kwargs)

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

    def get_success_url(self):
        message = '<strong>Operación Exitosa!</strong>\
        Se llevó a cabo con éxito la creación del\
        Grupo de Atención.'

        messages.add_message(
            self.request,
            messages.SUCCESS,
            message,
        )

        return reverse(
            'edita_grupo_atencion',
            kwargs={"pk": self.object.pk})


class GrupoAtencionUpdateView(UpdateView, GrupoAtencionMixin):

    template_name = 'grupo_atencion/grupo_atencion.html'
    model = GrupoAtencion
    context_object_name = 'grupo_atencion'
    form_class = GrupoAtencionForm
    formset_agente_grupo_atencion = AgentesGrupoAtencionFormSet

    def get_context_data(self, **kwargs):
        context = super(
            GrupoAtencionUpdateView, self).get_context_data(**kwargs)

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

    def get_success_url(self):
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

    #    def get_queryset(self):
    #        queryset = ListaContacto.objects.all()
    #        return queryset


class ListaContactoMixin(object):

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


class ListaContactoCreateView(CreateView, ListaContactoMixin):

    template_name = 'lista_contacto/nueva_edita_listas_contacto.html'
    model = ListaContacto
    context_object_name = 'lista_contacto'
    form_class = ListaContactoForm
    form_file = FileForm

    def get_context_data(self, **kwargs):
        context = super(
            ListaContactoCreateView, self).get_context_data(**kwargs)

        if 'form_file' not in context:
            context['form_file'] = self.form_file()
        return context

    def form_valid(self, form):
        return self.process_all_forms(form)

    def form_invalid(self, form):
        return self.process_all_forms(form)

    def get_success_url(self):
        message = '<strong>Operación Exitosa!</strong>\
        Se llevó a cabo con éxito la creación de\
        la Base de Datos de Contactos.'

        messages.add_message(
            self.request,
            messages.SUCCESS,
            message,
        )

        return reverse(
            'edita_lista_contacto',
            kwargs={"pk": self.object.pk})


class ListaContactoUpdateView(UpdateView, ListaContactoMixin):

    template_name = 'lista_contacto/nueva_edita_listas_contacto.html'
    model = ListaContacto
    context_object_name = 'lista_contacto'
    form_class = ListaContactoForm
    form_file = FileForm

    def get_context_data(self, **kwargs):
        context = super(
            ListaContactoUpdateView, self).get_context_data(**kwargs)

        if 'form_file' not in context:
            context['form_file'] = self.form_file()
        return context

    def form_valid(self, form):
        return self.process_all_forms(form)

    def form_invalid(self, form):
        return self.process_all_forms(form)

    def get_success_url(self):
        message = '<strong>Operación Exitosa!</strong>\
        Se llevó a cabo con éxito la actualización de\
        la Base de Datos de Contactos.'

        messages.add_message(
            self.request,
            messages.SUCCESS,
            message,
        )

        return reverse(
            'edita_lista_contacto',
            kwargs={"pk": self.object.pk})


#===============================================================================
# Campaña
#===============================================================================

class CampanaListView(ListView):
    """
    Lista las capañas que están activas.
    """

    template_name = 'campana/lista_campana.html'
    context_object_name = 'campanas'
    model = Campana

    def get_queryset(self):
        queryset = Campana.objects.obtener_activas()
        return queryset


class CampanaCreateView(CreateView):
    """
    Crea una nueva campaña. Por defecto
    u estado es EN_DEFICNICION
    """

    template_name = 'campana/nueva_edita_campana.html'
    model = Campana
    context_object_name = 'campana'
    form_class = CampanaForm

    def get_success_url(self):
        return reverse(
            'confirma_campana',
            kwargs={"pk": self.object.pk})


class ConfirmaCampanaView(UpdateView):
    """
    Confirma la creación de una campaña
    cambiando su estado a ACTIVA.
    Si la campaña ya esta activa, redirecciona
    a editar la campaña.
    """

    template_name = 'campana/confirma_campana.html'
    model = Campana
    context_object_name = 'campana'
    form_class = ConfirmaForm

    def get(self, request, *args, **kwargs):
        campana = self.get_object()
        if not campana.estado == Campana.ESTADO_EN_DEFINICION:
            return redirect('edita_campana', pk=campana.pk)
        return super(ConfirmaCampanaView, self).get(request, *args, **kwargs)

    def form_valid(self, form):
        if 'confirma' in self.request.POST:
            campana = self.object
            campana.activar()

            return redirect(self.get_success_url())
        elif 'cancela' in self.request.POST:
            pass
            #TODO: Implementar la cancelación.

    def get_success_url(self):
        message = '<strong>Operación Exitosa!</strong>\
        Se llevó a cabo con éxito la creación de\
        la Campaña.'

        messages.add_message(
            self.request,
            messages.SUCCESS,
            message,
        )

        return reverse('lista_campana')


class CampanaUpdateView(UpdateView):
    """
    Actualiza una campaña.
    """

    template_name = 'campana/nueva_edita_campana.html'
    model = Campana
    context_object_name = 'campana'
    form_class = CampanaForm

    def get_success_url(self):
        message = '<strong>Operación Exitosa!</strong>\
        Se llevó a cabo con éxito la actualización de\
        la Campaña.'

        messages.add_message(
            self.request,
            messages.SUCCESS,
            message,
        )

        return reverse(
            'edita_campana',
            kwargs={"pk": self.object.pk})


#===============================================================================
# Estados
#===============================================================================


class EstadoView(ListView):
    """
    Lista las capañas diferenciadas
    en sus estados.
    Pasa un diccionario al template
    con las claves como estados.
    """

    template_name = 'estado/estado.html'
    context_object_name = 'campanas'
    model = Campana

    def get_queryset(self):
        query_dict = {
            'activas': Campana.objects.obtener_activas(),
            'finalizadas': Campana.objects.obtener_finalizadas(),
        }
        return query_dict
