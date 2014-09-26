# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from django.contrib import messages
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect
from django.shortcuts import redirect, get_object_or_404
from django.views.generic.base import RedirectView
from django.views.generic.edit import DeleteView, CreateView, UpdateView
from django.views.generic.list import ListView
from django.views.generic.detail import DetailView
from fts_web.forms import TemplateForm
from fts_web.models import Campana
from fts_web.views_campana_creacion import (
    AudioCampanaCreateView, AudioCampanaOrdenView, AudiosCampanaDeleteView,
    CalificacionCampanaCreateView, CalificacionCampanaDeleteView,
    OpcionCampanaCreateView, OpcionCampanaDeleteView,
    ActuacionCampanaCreateView, ActuacionCampanaDeleteView,
    ConfirmaCampanaView)
from fts_web.views_campana_creacion import (CheckEstadoTemplateMixin,
                                            TemplateEnDefinicionMixin)
import logging as logging_


logger = logging_.getLogger(__name__)


# =============================================================================
# Templates
# =============================================================================

class TemplateMixin(object):

    def get_context_data(self, **kwargs):
        context = super(TemplateMixin, self).get_context_data(**kwargs)
        context['es_template'] = True
        return context


class TemplateListView(TemplateMixin, ListView):
    """
    Esta vista lista los objetos Capanas-->Templates activos.
    """

    template_name = 'template/lista_template.html'
    context_object_name = 'campanas'
    model = Campana

    def get_context_data(self, **kwargs):
        context = super(TemplateListView, self).get_context_data(**kwargs)
        context['templates_activos'] = \
            Campana.objects_template.obtener_activos()
        return context


class TemplateDeleteView(TemplateMixin, DeleteView):
    """
    Esta vista se encarga de la eliminación del
    objeto Campana-->Template.
    """

    model = Campana
    template_name = 'campana/elimina_campana.html'

    def dispatch(self, request, *args, **kwargs):
        self.campana = \
            Campana.objects_template.obtener_activo_para_eliminar_crear_ver(
                kwargs['pk_campana'])
        return super(TemplateDeleteView, self).dispatch(request, *args,
                                                        **kwargs)

    def get_object(self, queryset=None):
        return Campana.objects_template.obtener_activo_para_eliminar_crear_ver(
            self.kwargs['pk_campana'])

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        success_url = self.get_success_url()

        self.object.borrar_template()

        message = '<strong>Operación Exitosa!</strong>\
        Se llevó a cabo con éxito la eliminación del Template.'

        messages.add_message(
            self.request,
            messages.SUCCESS,
            message,
        )
        return HttpResponseRedirect(success_url)

    def get_success_url(self):
        return reverse('lista_template')


class TemplateCreateView(TemplateMixin, CreateView):
    """
    Esta vista crea un objeto Campana-->Template.
    Por defecto su estado es EN_DEFICNICION,
    Redirecciona a crear las opciones para esta
    Campana.
    """
    template_name = 'campana/nueva_edita_campana.html'
    model = Campana
    context_object_name = 'campana'
    form_class = TemplateForm

    def form_valid(self, form):
        self.object = form.save()

        self.object.es_template = True
        self.object.estado = Campana.ESTADO_TEMPLATE_EN_DEFINICION
        self.object.save()
        return redirect(self.get_success_url())

    def get_success_url(self):
        return reverse(
            'audio_template',
            kwargs={"pk_campana": self.object.pk})


class TemplateaUpdateView(CheckEstadoTemplateMixin, TemplateEnDefinicionMixin,
                          TemplateMixin, UpdateView):
    """
    Esta vista actualiza un objeto Campana-->Template.
    """

    template_name = 'campana/nueva_edita_campana.html'
    model = Campana
    context_object_name = 'campana'
    form_class = TemplateForm

    # @@@@@@@@@@@@@@@@@@@@

    def get_success_url(self):
        return reverse(
            'audio_template',
            kwargs={"pk_campana": self.object.pk})


class DetalleTemplateView(TemplateMixin, DetailView):
    template_name = 'campana/detalle_campana.html'
    context_object_name = 'campana'
    pk_url_kwarg = 'pk_campana'
    model = Campana

    def dispatch(self, request, *args, **kwargs):
        self.campana = \
            Campana.objects_template.obtener_activo_para_eliminar_crear_ver(
                kwargs['pk_campana'])
        return super(DetalleTemplateView, self).dispatch(request, *args,
                                                         **kwargs)

    def get_object(self, queryset=None):
        return Campana.objects_template.obtener_activo_para_eliminar_crear_ver(
            self.kwargs['pk_campana'])


class AudioTemplateCreateView(CheckEstadoTemplateMixin, TemplateMixin,
                              AudioCampanaCreateView):

    # @@@@@@@@@@@@@@@@@@@@

    def get_success_url(self):
        return reverse(
            'audio_template',
            kwargs={"pk_campana": self.campana.pk})


class AudioTemplateOrdenView(CheckEstadoTemplateMixin, TemplateMixin,
                             AudioCampanaOrdenView):
    def redirecciona_a_audios_campana(self):
        url = reverse('audio_template', kwargs={"pk_campana": self.campana.pk})
        return HttpResponseRedirect(url)


class AudiosTemplateDeleteView(CheckEstadoTemplateMixin, TemplateMixin,
                               AudiosCampanaDeleteView):

    def get_success_url(self):
        return reverse('audio_template',
                       kwargs={"pk_campana": self.campana.pk})


class CalificacionTemplateCreateView(CheckEstadoTemplateMixin,
                                     TemplateEnDefinicionMixin, TemplateMixin,
                                     CalificacionCampanaCreateView):

    # @@@@@@@@@@@@@@@@@@@@

    def get_success_url(self):
        return reverse(
            'calificacion_template',
            kwargs={"pk_campana": self.kwargs['pk_campana']}
        )


class CalificacionTemplateDeleteView(CheckEstadoTemplateMixin, TemplateMixin,
                                     CalificacionCampanaDeleteView):

    # @@@@@@@@@@@@@@@@@@@@

    def get_success_url(self):
        return reverse(
            'calificacion_template',
            kwargs={"pk_campana": self.campana.pk}
        )


class OpcionTemplateCreateView(CheckEstadoTemplateMixin,
                               TemplateEnDefinicionMixin, TemplateMixin,
                               OpcionCampanaCreateView):

    # @@@@@@@@@@@@@@@@@@@@

    def get_success_url(self):
        return reverse(
            'opcion_template',
            kwargs={"pk_campana": self.kwargs['pk_campana']}
        )


class OpcionTemplateDeleteView(CheckEstadoTemplateMixin, TemplateMixin,
                               OpcionCampanaDeleteView):

    # @@@@@@@@@@@@@@@@@@@@

    def get_success_url(self):
        return reverse(
            'opcion_template',
            kwargs={"pk_campana": self.campana.pk}
        )


class ActuacionTemplateCreateView(CheckEstadoTemplateMixin,
                                  TemplateEnDefinicionMixin, TemplateMixin,
                                  ActuacionCampanaCreateView):

    # @@@@@@@@@@@@@@@@@@@@

    def get_success_url(self):
        return reverse(
            'actuacion_template',
            kwargs={"pk_campana": self.kwargs['pk_campana']}
        )

    def form_valid(self, form):
        self.object = form.save()
        return redirect(self.get_success_url())


class ActuacionTemplateDeleteView(CheckEstadoTemplateMixin, TemplateMixin,
                                  ActuacionCampanaDeleteView):

    # @@@@@@@@@@@@@@@@@@@@

    def get_success_url(self):
        return reverse(
            'actuacion_template',
            kwargs={"pk_campana": self.campana.pk}
        )

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        success_url = self.get_success_url()
        self.object.delete()

        message = '<strong>Operación Exitosa!</strong>\
        Se llevó a cabo con éxito la eliminación de la Actuación.'

        messages.add_message(
            self.request,
            messages.SUCCESS,
            message,
        )

        return HttpResponseRedirect(success_url)


class ConfirmaTemplateView(CheckEstadoTemplateMixin, TemplateEnDefinicionMixin,
                           TemplateMixin, ConfirmaCampanaView):

    def get_success_url(self):
        return reverse('lista_template')


class CreaCampanaTemplateView(TemplateMixin, RedirectView):
    permanent = False
    url = None

    def dispatch(self, request, *args, **kwargs):
        self.campana = \
            Campana.objects_template.obtener_activo_para_eliminar_crear_ver(
                kwargs['pk_campana'])
        return super(CreaCampanaTemplateView, self).dispatch(request, *args,
                                                             **kwargs)

    def get(self, request, *args, **kwargs):
        template = get_object_or_404(
            Campana, pk=self.kwargs['pk_campana']
        )
        campana = Campana.objects_template.crea_campana_de_template(template)

        self.url = reverse('datos_basicos_campana',
                           kwargs={"pk_campana": campana.pk})

        return super(CreaCampanaTemplateView, self).get(request, *args,
                                                        **kwargs)
