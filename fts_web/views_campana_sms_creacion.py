# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import json

from django.contrib import messages
from django.core.urlresolvers import reverse
from django.db import transaction
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import redirect, get_object_or_404
from django.views.generic.edit import (CreateView, UpdateView, DeleteView,
                                       BaseUpdateView)

from fts_web.forms import (CampanaForm, CampanaSmsForm,
    ActuacionForm, ActuacionSmsForm, OpcionSmsForm,
    TemplateMensajeCampanaSmsForm)
from fts_web.models import (Campana, CampanaSms, OpcionSms,
    Actuacion, ActuacionSms)

from fts_web.services.creacion_campana_sms import (
    ConfirmacionCampanaSmsService, ValidarCampanaSmsError)

import logging as logging_


logger = logging_.getLogger(__name__)


class CheckEstadoCampanaSmsMixin(object):
    """Mixin para utilizar en las vistas de creación de campañas.
    Utiliza `Campana.objects.obtener_en_definicion_para_editar()`
    para obtener la campaña pasada por url.
    Este metodo falla si la campaña no deberia ser editada.
    ('editada' en el contexto del proceso de creacion de la campaña)
    """

    def dispatch(self, request, *args, **kwargs):
        self.campana_sms = \
            CampanaSms.objects.obtener_en_definicion_para_editar(
                self.kwargs['pk_campana_sms'])

        return super(CheckEstadoCampanaSmsMixin, self).dispatch(request, *args,
                                                             **kwargs)


class CampanaSmsCreateView(CreateView):
    """
    Esta vista crea un objeto CampanaSms.
    """

    template_name = 'campana_sms/nueva_edita_campana_sms.html'
    model = CampanaSms
    context_object_name = 'campana_sms'
    form_class = CampanaSmsForm

    def form_valid(self, form):
        self.object = form.save(commit=False)

        # TODO: Cambiar la creación del identificador y pasarla a un servicio.
        try:
            identificador = \
                CampanaSms.objects.latest('id').identificador_campana_sms + 1
        except CampanaSms.DoesNotExist:
            identificador = 1000

        self.object.identificador_campana_sms = identificador
        self.object.save()

        return super(CampanaSmsCreateView, self).form_valid(form)

    def get_success_url(self):
        return reverse('template_mensaje_campana_sms',
                       kwargs={"pk_campana_sms": self.object.pk})


class CampanaSmsUpdateView(CheckEstadoCampanaSmsMixin, UpdateView):
    """
    Esta vista actualiza un objeto CampanaSms.
    """

    template_name = 'campana_sms/nueva_edita_campana_sms.html'
    model = CampanaSms
    context_object_name = 'campana_sms'
    pk_url_kwarg = 'pk_campana_sms'
    form_class = CampanaSmsForm

    def get_success_url(self):
        return reverse(
            'template_mensaje_campana_sms',
            kwargs={"pk_campana_sms": self.object.pk})


class TemplateMensajeCampanaSmsUpdateView(CheckEstadoCampanaSmsMixin,
                                          UpdateView):
    """
    Esta vista actualiza un objeto CampanaSms, agregando
    el cuerpo del mensaje.
    """

    template_name = 'campana_sms/template_mensaje_campana_sms.html'
    model = CampanaSms
    context_object_name = 'campana_sms'
    pk_url_kwarg = 'pk_campana_sms'
    form_class = TemplateMensajeCampanaSmsForm

    def get_success_url(self):
        return reverse(
            'template_mensaje_campana_sms',
            kwargs={"pk_campana_sms": self.object.pk})


class OpcionSmsCampanaSmsCreateView(CheckEstadoCampanaSmsMixin, CreateView):
    """
    """

    template_name = 'campana_sms/opciones_campana_sms.html'
    model = OpcionSms
    form_class = OpcionSmsForm

    def get_initial(self):
        initial = super(OpcionSmsCampanaSmsCreateView, self).get_initial()
        initial.update({'campana_sms': self.campana_sms.id})
        return initial

    def get_context_data(self, **kwargs):
        context = super(
            OpcionSmsCampanaSmsCreateView, self).get_context_data(**kwargs)
        context['campana_sms'] = self.campana_sms
        return context

    def get_success_url(self):
        return reverse(
            'opcion_sms_campana_sms',
            kwargs={"pk_campana_sms": self.kwargs['pk_campana_sms']})


class OpcionSmsCampanaSmsDeleteView(CheckEstadoCampanaSmsMixin, DeleteView):
    """
    Esta vista se encarga de la eliminación del
    objeto OpcionSms seleccionado.
    """

    model = OpcionSms
    template_name = 'campana_sms/elimina_opcion_sms_campana_sms.html'

    def delete(self, request, *args, **kwargs):
        message = '<strong>Operación Exitosa!</strong>\
            Se llevó a cabo con éxito la eliminación de la Respuesta.'

        messages.add_message(
            self.request,
            messages.SUCCESS,
            message,
        )
        return super(OpcionSmsCampanaSmsDeleteView, self).delete(request,
                                                           *args, **kwargs)

    def get_success_url(self):
        return reverse(
            'opcion_sms_campana_sms',
            kwargs={"pk_campana_sms": self.kwargs['pk_campana_sms']})


class ActuacionSmsCampanaSmsCreateView(CheckEstadoCampanaSmsMixin, CreateView):
    """
    """

    template_name = 'campana_sms/actuacion_sms_campana_sms.html'
    model = ActuacionSms
    context_object_name = 'actuacion_sms'
    form_class = ActuacionSmsForm

    def get_initial(self):
        initial = super(ActuacionSmsCampanaSmsCreateView, self).get_initial()
        initial.update({'campana_sms': self.campana_sms.id})
        return initial

    def get_context_data(self, **kwargs):
        context = super(
            ActuacionSmsCampanaSmsCreateView, self).get_context_data(**kwargs)
        context['campana_sms'] = self.campana_sms
        context['actuaciones_validas'] = \
            self.campana_sms.obtener_actuaciones_validas()
        return context

    def form_valid(self, form):
        form_valid = super(ActuacionSmsCampanaSmsCreateView, self).form_valid(
            form)

        if not self.campana_sms.valida_actuaciones():
            message = """<strong>¡Cuidado!</strong>
            Los días del rango de fechas seteados en la campaña NO coinciden
            con ningún día de las actuaciones programadas. Por consiguiente
            la campaña NO se ejecutará."""
            messages.add_message(
                self.request,
                messages.WARNING,
                message,
            )

        return form_valid

    def get_success_url(self):
        return reverse(
            'actuacion_sms_campana_sms',
            kwargs={"pk_campana_sms": self.kwargs['pk_campana_sms']})


class ActuacionSmsCampanaSmsDeleteView(CheckEstadoCampanaSmsMixin, DeleteView):
    """
    Esta vista se encarga de la eliminación del
    objeto ActuacionSms seleccionado.
    """

    model = ActuacionSms
    template_name = 'campana_sms/elimina_actuacion_sms_campana_sms.html'

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        success_url = self.get_success_url()
        self.object.delete()

        if not self.campana_sms.valida_actuaciones():
            message = """<strong>¡Cuidado!</strong>
            Los días del rango de fechas seteados en la campaña NO coinciden
            con ningún día de las actuaciones programadas. Por consiguiente
            la campaña NO se ejecutará."""
            messages.add_message(
                self.request,
                messages.WARNING,
                message,
            )

        message = '<strong>Operación Exitosa!</strong>\
        Se llevó a cabo con éxito la eliminación de la Actuación.'

        messages.add_message(
            self.request,
            messages.SUCCESS,
            message,
        )
        return HttpResponseRedirect(success_url)

    def get_success_url(self):
        return reverse(
            'actuacion_sms_campana_sms',
            kwargs={"pk_campana_sms": self.kwargs['pk_campana_sms']})


class ConfirmaCampanaSmsMixin(object):

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()

        confirmacion_campana_sms_service = ConfirmacionCampanaSmsService()

        try:
            confirmacion_campana_sms_service.confirmar(self.object)
        except ValidarCampanaSmsError, e:
            message = ("<strong>Operación Errónea!</strong> "
                       "No se pudo confirmar la creación de la campaña debido "
                       "al siguiente error: {0}".format(e))
            messages.add_message(
                self.request,
                messages.ERROR,
                message,
            )
            return self.render_to_response(self.get_context_data())
        else:
            message = ("<strong>Operación Exitosa!</strong> "
                       "Se llevó a cabo con éxito la creación de la "
                       "Campaña Sms.")
            messages.add_message(
                self.request,
                messages.SUCCESS,
                message,
            )
            return redirect(self.get_success_url())

    def get_success_url(self):
        return reverse('nueva_campana_sms')


class ConfirmaCampanaSmsView(ConfirmaCampanaSmsMixin,
                             CheckEstadoCampanaSmsMixin, UpdateView):
    """
    Esta vista confirma la creación de un objeto
    CampanaSms. Imprime el resumen del objeto y si
    es aceptado.
    """

    template_name = 'campana_sms/confirma_campana_sms.html'
    model = CampanaSms
    pk_url_kwarg = 'pk_campana_sms'
    context_object_name = 'campana_sms'
