# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from django.contrib import messages
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect
from django.shortcuts import redirect, get_object_or_404
from django.views.generic.edit import FormView, UpdateView, CreateView, \
    DeleteView
from fts_web.errors import FtsRecicladoCampanaError
from fts_web.forms import TipoRecicladoCampanaSmsForm, CampanaForm, ActuacionForm
from fts_web.models import CampanaSms, Actuacion
from fts_web.reciclador_base_datos_contacto.reciclador import (
    RecicladorBaseDatosContacto, CampanaEstadoInvalidoError,
    CampanaTipoRecicladoInvalidoError, FtsRecicladoBaseDatosContactoError)
from fts_web.views_campana_creacion import (ConfirmaCampanaView,
                                            CheckEstadoCampanaMixin,
                                            CampanaEnDefinicionMixin)

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

        tipos_reciclado = tipo_reciclado_unico

        try:
            # Utiliza la capa de servicio para la creación de la base de datos
            # reciclada que usara la campana que se está reciclando.
            reciclador_base_datos_contacto = RecicladorBaseDatosContacto()
            bd_contacto_reciclada = reciclador_base_datos_contacto.\
                reciclar_campana_sms(self.campana_id, tipos_reciclado)

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
                self.campana_reciclada = CampanaSms.objects.reciclar_campana(
                    self.campana_sms_id, bd_contacto_reciclada)
            except FtsRecicladoCampanaError:
                # TODO: En esta excepción verificar si la BD generada,
                # es una "nueva" en la que se reciclaron contactos,
                # o si es la misma de la campana original. Si es una "nueva"
                # definir si se borra o que acción se realiza.

                message = '<strong>Operación Errónea!</strong>\
                No se pudo reciclar la Campana.'

                messages.add_message(
                    self.request,
                    messages.ERROR,
                    message,
                )
                return self.form_invalid(form)

        return super(TipoRecicladoCampanaSmsView, self).form_valid(form)

    def get_success_url(self):
        return reverse(
            'redefinicion_reciclado_campana',
            kwargs={"pk_campana_sms": self.campana_reciclada.pk}
        )
