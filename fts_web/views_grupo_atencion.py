# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from django.contrib import messages
from django.core.urlresolvers import reverse
from django.db import transaction
from django.http.response import HttpResponseRedirect
from django.shortcuts import redirect
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from fts_daemon.asterisk_config import create_queue_config_file, reload_config
from fts_web.forms import GrupoAtencionForm, AgentesGrupoAtencionFormSet
from fts_web.models import GrupoAtencion
import logging as logging_


logger = logging_.getLogger(__name__)


class GrupoAtencionMixin(object):
    """
    Este mixin procesa y valida
    los formularios en la creación y edición
    de objetos GrupoAtencion.
    """

    @transaction.atomic(savepoint=False)
    def process_all_forms_in_tx(self, form, update=False):
        """
        Este método se encarga de validar el
        formularios GrupoAtencionForm y hacer
        el save. Luego instancia el formset
        AgentesGrupoAtencionFormSet con el
        objeto creado y si es válido realiza
        el save.
        """

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

            message = '<strong>Operación Exitosa!</strong>\
            Se llevó a cabo con éxito la operación.'

            messages.add_message(
                self.request,
                messages.SUCCESS,
                message,
            )

            try:
                create_queue_config_file()
            except:
                logger.exception("GrupoAtencionMixin: error al intentar "
                    "create_queue_config_file()")
                messages.add_message(
                    self.request,
                    messages.ERROR,
                    "Atencion: hubo un inconveniente al generar "
                    "la configuracion de Asterisk (queues). "
                    "Por favor, contáctese con el administrador "
                    "del sistema."
                )

            try:
                ret = reload_config()
                if ret != 0:
                    messages.add_message(
                        self.request,
                        messages.ERROR,
                        "Atencion: hubo un inconveniente al intentar "
                        "recargar la configuracion de Asterisk. "
                        "Por favor, contáctese con el administrador "
                        "del sistema."
                    )
            except:
                logger.exception("GrupoAtencionMixin: error al intentar "
                    "reload_config()")
                messages.add_message(
                    self.request,
                    messages.ERROR,
                    "Atencion: hubo un inconveniente al intentar "
                    "recargar la configuracion de Asterisk. "
                    "Por favor, contáctese con el administrador "
                    "del sistema."
                )

            return redirect(self.get_success_url())
        else:
            if form.is_valid() and not update:
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
    """
    Esta vista crea un objeto GrupoAtencion.
    """

    template_name = 'derivacion/grupo_atencion.html'
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
        return self.process_all_forms_in_tx(form)

    def form_invalid(self, form):
        return self.process_all_forms_in_tx(form)

    def get_success_url(self):
        return reverse('lista_derivacion')


class GrupoAtencionUpdateView(UpdateView, GrupoAtencionMixin):
    """
    Esta vista actualiza el objeto GrupoAtencion
    seleccionado.
    """

    template_name = 'derivacion/grupo_atencion.html'
    model = GrupoAtencion
    context_object_name = 'grupo_atencion'
    form_class = GrupoAtencionForm
    formset_agente_grupo_atencion = AgentesGrupoAtencionFormSet
    queryset = GrupoAtencion.objects.all()

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
        return self.process_all_forms_in_tx(form, update=True)

    def form_invalid(self, form):
        return self.process_all_forms_in_tx(form, update=True)

    def get_success_url(self):
        return reverse('lista_derivacion')


class GrupoAtencionDeleteView(DeleteView):
    """
    Esta vista se encarga de la eliminación del
    objeto GrupAtencion seleccionado.
    """

    model = GrupoAtencion
    template_name = 'derivacion/elimina_grupo_atencion.html'
    queryset = GrupoAtencion.objects.all()

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        success_url = self.get_success_url()

        # Marcamos el grupo de atención como borrado.
        self.object.borrar()

        message = '<strong>Operación Exitosa!</strong>\
        Se llevó a cabo con éxito la eliminación del Grupo de Atención.'

        messages.add_message(
            self.request,
            messages.SUCCESS,
            message,
        )
        return HttpResponseRedirect(success_url)

    def get_success_url(self):
        return reverse('lista_derivacion')
