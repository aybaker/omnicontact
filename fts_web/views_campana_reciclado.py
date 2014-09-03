# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from django.contrib import messages
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect
from django.shortcuts import redirect, get_object_or_404
from django.views.generic.edit import FormView, UpdateView, CreateView, \
    DeleteView
from fts_web.errors import FtsRecicladoCampanaError
from fts_web.forms import TipoRecicladoForm, CampanaForm, ActuacionForm
from fts_web.models import Campana, Actuacion
from fts_web.reciclador_base_datos_contacto.reciclador import (
    RecicladorBaseDatosContacto, CampanaEstadoInvalidoError,
    CampanaTipoRecicladoInvalidoError, FtsRecicladoBaseDatosContactoError)
from fts_web.views_campana_creacion import ConfirmaCampanaMixin
import logging as logging_


logger = logging_.getLogger(__name__)


class TipoRecicladoCampanaView(FormView):
    """
    Esta vista presenta la elección del tipo de reciclado iniciando el
    proceso de reciclado de una camapan.
    """

    template_name = 'campana/reciclado/campana_tipo_reciclado.html'
    form_class = TipoRecicladoForm

    # @@@@@@@@@@@@@@@@@@@@

    def post(self, request, *args, **kwargs):
        self.campana_id = kwargs['pk']
        return super(TipoRecicladoCampanaView, self).post(request, args,
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
            bd_contacto_reciclada = reciclador_base_datos_contacto.reciclar(
                self.campana_id, tipos_reciclado)

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
                self.campana_reciclada = Campana.objects.reciclar_campana(
                    self.campana_id, bd_contacto_reciclada)
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

        return super(TipoRecicladoCampanaView, self).form_valid(form)

    def get_success_url(self):
        return reverse(
            'redefinicion_reciclado_campana',
            kwargs={"pk": self.campana_reciclada.pk}
        )


class RedefinicionRecicladoCampanaView(UpdateView):
    """
    Esta vista se encarga de redefinir la campana a reciclar.
    """

    template_name = 'campana/reciclado/redefinicion_reciclado_campana.html'
    model = Campana
    context_object_name = 'campana'
    form_class = CampanaForm

    # @@@@@@@@@@@@@@@@@@@@

    def get(self, request, *args, **kwargs):
        """
        Valida que la campana a redefinir este en definición.
        """
        campana = self.get_object()
        if not campana.estado == Campana.ESTADO_EN_DEFINICION:
            return redirect('lista_campana')
        return super(RedefinicionRecicladoCampanaView, self).get(
            request, *args, **kwargs)

    def get_form(self, form_class):
        return form_class(reciclado=True, **self.get_form_kwargs())

    def get_success_url(self):
        campana = self.get_object()
        if not campana.valida_actuaciones():
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
            'actuacion_reciclado_campana',
            kwargs={"pk": self.object.pk}
        )


class ActuacionRecicladoCampanaView(CreateView):
    """
    Esta vista crea uno o varios objetos Actuacion
    para la Campana reciclada que se este creando.
    Inicializa el form con campo campana (hidden)
    con el id de campana que viene en la url.
    """

    # @@@@@@@@@@@@@@@@@@@@

    template_name = 'campana/reciclado/actuacion_reciclado_campana.html'
    model = Actuacion
    context_object_name = 'actuacion'
    form_class = ActuacionForm

    def get_initial(self):
        initial = super(ActuacionRecicladoCampanaView, self).get_initial()
        if 'pk' in self.kwargs:
            initial.update({
                'campana': self.kwargs['pk'],
            })
        return initial

    def get_context_data(self, **kwargs):
        context = super(
            ActuacionRecicladoCampanaView, self).get_context_data(**kwargs)

        self.campana = get_object_or_404(
            Campana, pk=self.kwargs['pk']
        )
        context['campana'] = self.campana
        context['actuaciones_validas'] =\
            self.campana.obtener_actuaciones_validas()
        return context

    def form_valid(self, form):
        form_valid = super(ActuacionRecicladoCampanaView, self).form_valid(
            form)

        self.campana = get_object_or_404(
            Campana, pk=self.kwargs['pk']
        )

        if not self.campana.valida_actuaciones():
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
            'actuacion_reciclado_campana',
            kwargs={"pk": self.kwargs['pk']}
        )


class ActuacionRecicladoCampanaDeleteView(DeleteView):
    """
    Esta vista se encarga de la eliminación del
    objeto Actuación seleccionado.
    """

    model = Actuacion
    template_name = \
        'campana/reciclado/elimina_actuacion_reciclado_campana.html'

    # @@@@@@@@@@@@@@@@@@@@

    def get_object(self, queryset=None):
        actuacion = super(ActuacionRecicladoCampanaDeleteView, self).\
            get_object(queryset=None)

        self.campana = actuacion.campana
        return actuacion

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        success_url = self.get_success_url()
        self.object.delete()

        if not self.campana.valida_actuaciones():
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
            'actuacion_reciclado_campana',
            kwargs={"pk": self.campana.pk}
        )


class ConfirmaRecicladoCampanaView(ConfirmaCampanaMixin):
    template_name = 'campana/reciclado/confirma_reciclado_campana.html'

    # @@@@@@@@@@@@@@@@@@@@

    def get(self, request, *args, **kwargs):
        campana = self.get_object()
        if not campana.confirma_campana_valida():
            message = """<strong>¡Cuidado!</strong>
            La campana posee datos inválidos y no pude ser confirmada.
            Verifique que todos los datos requeridos sean válidos."""
            messages.add_message(
                self.request,
                messages.WARNING,
                message,
            )

            return HttpResponseRedirect(
                reverse(
                    'actuacion_reciclado_campana',
                    kwargs={"pk": campana.pk}))
        return super(ConfirmaRecicladoCampanaView, self).get(
            request, *args, **kwargs)
