# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from django.contrib import messages
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect
from django.shortcuts import redirect, get_object_or_404
from django.views.generic.edit import FormView, UpdateView, CreateView, \
    DeleteView
from fts_web.errors import FtsRecicladoCampanaError
from fts_web.forms import (TipoRecicladoCampanaSmsForm, CampanaSmsForm,
                           ActuacionSmsForm)
from fts_web.models import CampanaSms, ActuacionSms
from fts_web.reciclador_base_datos_contacto.reciclador import (
    RecicladorBaseDatosContacto, CampanaEstadoInvalidoError,
    CampanaTipoRecicladoInvalidoError, FtsRecicladoBaseDatosContactoError)
from fts_web.views_campana_sms_creacion import (ConfirmaCampanaSmsView,
                                                CheckEstadoCampanaSmsMixin)

import logging as logging_


logger = logging_.getLogger(__name__)


class TipoRecicladoCampanaSmsView(FormView):
    """
    Esta vista presenta la elección del tipo de reciclado iniciando el
    proceso de reciclado de una campana sms.
    """

    template_name = 'campana_sms/reciclado/campana_sms_tipo_reciclado.html'
    form_class = TipoRecicladoCampanaSmsForm

    # @@@@@@@@@@@@@@@@@@@@

    def dispatch(self, request, *args, **kwargs):
        # Valida que la campana este en el estado depurada para renderizar
        # el template.
        CampanaSms.objects.obtener_campana_sms_para_reciclar(
            self.kwargs['pk_campana_sms'])

        return super(TipoRecicladoCampanaSmsView, self).dispatch(request, *args,
                                                            **kwargs)

    def post(self, request, *args, **kwargs):
        self.campana_sms_id = kwargs['pk_campana_sms']
        return super(TipoRecicladoCampanaSmsView, self).post(request, args,
                                                          kwargs)

    def form_valid(self, form):
        # TODO: Validar y mostrar error si no lo hace.
        tipo_reciclado_unico = list(form.cleaned_data['tipo_reciclado_unico'])
        tipo_reciclado_conjunto = form.cleaned_data['tipo_reciclado_conjunto']
        assert not (len(tipo_reciclado_unico) and len(tipo_reciclado_conjunto))
        assert (len(tipo_reciclado_unico) or len(tipo_reciclado_conjunto))

        tipos_reciclado = tipo_reciclado_unico
        if tipo_reciclado_conjunto:
            tipos_reciclado = tipo_reciclado_conjunto

        try:
            # Utiliza la capa de servicio para la creación de la base de datos
            # reciclada que usara la campana que se está reciclando.
            reciclador_base_datos_contacto = RecicladorBaseDatosContacto()
            bd_contacto_reciclada = reciclador_base_datos_contacto.\
                reciclar_campana_sms(self.campana_sms_id, tipos_reciclado)

        except (CampanaEstadoInvalidoError,
                CampanaTipoRecicladoInvalidoError,
                FtsRecicladoBaseDatosContactoError) as error:
            message = '<strong>Operación Errónea!</strong>\
            No se pudo reciclar la Base de Datos de la campana. {0}'.format(
                error)

            messages.add_message(
                self.request,
                messages.ERROR,
                message,
            )
            return self.form_invalid(form)
        else:
            try:
                # Intenta reciclar la campana con el tipo de reciclado
                # seleccionado.
                self.campana_reciclada = CampanaSms.objects.\
                    reciclar_campana_sms(self.campana_sms_id,
                                         bd_contacto_reciclada)

            except FtsRecicladoCampanaError:
                # TODO: En esta excepción verificar si la BD generada,
                # es una "nueva" en la que se reciclaron contactos,
                # o si es la misma de la campana original. Si es una "nueva"
                # definir si se borra o que acción se realiza.

                message = '<strong>Operación Errónea!</strong>\
                No se pudo reciclar la Campana SMS.'

                messages.add_message(
                    self.request,
                    messages.ERROR,
                    message,
                )
                return self.form_invalid(form)

        return super(TipoRecicladoCampanaSmsView, self).form_valid(form)

    def get_success_url(self):
        return reverse(
            'redefinicion_reciclado_campana_sms',
            kwargs={"pk_campana_sms": self.campana_reciclada.pk}
        )


class RedefinicionRecicladoCampanaSmsView(CheckEstadoCampanaSmsMixin,
                                          UpdateView):
    """
    Esta vista se encarga de redefinir la campana sms a reciclar.
    """

    template_name = 'campana_sms/reciclado/redefinicion_reciclado_campana_sms.html'
    model = CampanaSms
    context_object_name = 'campana_sms'
    form_class = CampanaSmsForm
    pk_url_kwarg = 'pk_campana_sms'

    # @@@@@@@@@@@@@@@@@@@@

    def get_form(self, form_class):
        return form_class(reciclado=True, **self.get_form_kwargs())

    def get_success_url(self):
        campana_sms = self.get_object()
        if not campana_sms.valida_actuaciones():
            message = """<strong>¡Cuidado!</strong>
            Los días del rango de fechas seteados en la campaña NO coinciden
            con ningún día de las actuaciones programadas. Por consiguiente
            la campaña NO se ejecutará."""
            messages.add_message(
                self.request,
                messages.WARNING,
                message,
            )

        return reverse(
            'actuacion_reciclado_campana_sms',
            kwargs={"pk_campana_sms": self.object.pk}
        )


class ActuacionRecicladoCampanaSmsView(CheckEstadoCampanaSmsMixin, CreateView):
    """
    Esta vista crea uno o varios objetos Actuacion
    para la Campana reciclada que se este creando.
    Inicializa el form con campo campana (hidden)
    con el id de campana que viene en la url.
    """

    # @@@@@@@@@@@@@@@@@@@@

    template_name = 'campana_sms/reciclado/actuacion_reciclado_campana_sms.html'
    model = ActuacionSms
    context_object_name = 'actuacion_sms'
    form_class = ActuacionSmsForm

    def get_initial(self):
        initial = super(ActuacionRecicladoCampanaSmsView, self).get_initial()
        initial.update({'campana_sms': self.kwargs['pk_campana_sms']})
        return initial

    def get_context_data(self, **kwargs):
        context = super(
            ActuacionRecicladoCampanaSmsView, self).get_context_data(**kwargs)

        context['campana_sms'] = self.campana_sms
        context['actuaciones_validas'] =\
            self.campana_sms.obtener_actuaciones_validas()
        return context

    def form_valid(self, form):
        form_valid = super(ActuacionRecicladoCampanaSmsView, self).form_valid(
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
            'actuacion_reciclado_campana_sms',
            kwargs={"pk_campana_sms": self.kwargs['pk_campana_sms']}
        )


class ActuacionRecicladoCampanaSmsDeleteView(CheckEstadoCampanaSmsMixin, DeleteView):
    """
    Esta vista se encarga de la eliminación del
    objeto Actuación seleccionado.
    """

    model = ActuacionSms
    template_name = \
        'campana_sms/reciclado/elimina_actuacion_reciclado_campana_sms.html'

    # @@@@@@@@@@@@@@@@@@@@

    def get_object(self, queryset=None):
        actuacion = super(ActuacionRecicladoCampanaSmsDeleteView, self).\
            get_object(queryset=None)
        return actuacion

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
            'actuacion_reciclado_campana_sms',
            kwargs={"pk_campana_sms": self.campana_sms.pk}
        )


class ConfirmaRecicladoCampanaSmsView(ConfirmaCampanaSmsView):
    template_name = 'campana_sms/reciclado/confirma_reciclado_campana_sms.html'