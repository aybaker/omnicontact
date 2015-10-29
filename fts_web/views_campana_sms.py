# -*- coding: utf-8 -*-

from __future__ import unicode_literals


from django.contrib import messages
from django.views.generic import DetailView, DeleteView
from django.views.generic.list import ListView
from django.http import HttpResponseRedirect
from django.core.urlresolvers import reverse
from fts_web.models import CampanaSms
from fts_web.services.datos_sms import FtsWebContactoSmsManager
from fts_web.services.estadisticas_campana_sms import \
    EstadisticasCampanaSmsService

import logging as logging_

logger = logging_.getLogger(__name__)


# =============================================================================
# Campaña SMS
# =============================================================================


class CampanaSmsListView(ListView):
    """
    Esta vista lista los objetos CapanasSms
    diferenciadas por sus estados actuales.
    Pasa un diccionario al template
    con las claves como estados.
    """

    template_name = 'campana_sms/lista_campana_sms.html'
    context_object_name = 'campanas_sms'
    model = CampanaSms

    def get_context_data(self, **kwargs):
        context = super(CampanaSmsListView, self).get_context_data(
           **kwargs)
        context['confirmadas'] = CampanaSms.objects.obtener_confirmadas()
        context['pausadas'] = CampanaSms.objects.obtener_pausadas()
        return context


class DetalleCampanSmsView(DetailView):
    """
    Muestra el detalle de la campaña sms.
    """
    template_name = 'campana_sms/detalle_campana_sms.html'
    context_object_name = 'campana_sms'
    pk_url_kwarg = 'pk_campana_sms'
    model = CampanaSms

    def dispatch(self, request, *args, **kwargs):
        self.campana_sms = \
            CampanaSms.objects.obtener_para_detalle(kwargs['pk_campana_sms'])
        return super(DetalleCampanSmsView, self).dispatch(request, *args,
                                                       **kwargs)

    def get_object(self, queryset=None):
        return CampanaSms.objects.obtener_para_detalle(
            self.kwargs['pk_campana_sms'])


class CampanaSmsDeleteView(DeleteView):
    """
    Esta vista se encarga de la eliminación del
    objeto Campana.
    """

    model = CampanaSms
    context_object_name = 'campana_sms'
    template_name = 'campana_sms/elimina_campana_sms.html'

    def dispatch(self, request, *args, **kwargs):
        self.campana_sms = \
            CampanaSms.objects.obtener_pausada_para_eliminar(
                kwargs['pk_campana_sms'])
        return super(CampanaSmsDeleteView, self).dispatch(request, *args,
                                                          **kwargs)

    def get_object(self, queryset=None):
        return CampanaSms.objects.obtener_pausada_para_eliminar(
            self.kwargs['pk_campana_sms'])

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        success_url = self.get_success_url()

        # Marcamos la campaña como borrada. Lo hacemos primero para que,
        # en caso de error, la excepcion se lance lo antes posible
        self.object.borrar()

        # Eliminamos la tabla fts_web_contwcto generada por el demonio sms.
        service_datos_sms = FtsWebContactoSmsManager()
        service_datos_sms.eliminar_tabla_fts_web_contacto(self.object)

        message = '<strong>Operación Exitosa!</strong>\
        Se llevó a cabo con éxito la eliminación de la Campaña SMS.'

        messages.add_message(
            self.request,
            messages.SUCCESS,
            message,
        )
        return HttpResponseRedirect(success_url)

    def get_success_url(self):
        return reverse('lista_campana_sms')


# =============================================================================
# Reporte
# =============================================================================


class CampanaSmsReporteListView(ListView):
    """
    Esta vista lista las campañas finalizadas con
    un resumen de sus características.
    """

    template_name = 'reporte/reporte_sms.html'
    context_object_name = 'campana_sms'
    model = CampanaSms

    def get_context_data(self, **kwargs):
        context = super(CampanaSmsReporteListView, self).get_context_data(
            **kwargs)
        context['campanas_reportes'] = CampanaSms.objects.\
            obtener_pausadas_confirmadas_para_reportes()
        return context


class CampanaReporteSmsEnviadosListView(ListView):
    """
    Muestra un listado de contactos a los cuales se le enviaron o se estan
    por enviar mensajes de texto
    """
    template_name = 'reporte/detalle_reporte_sms_enviado.html'
    context_object_name = 'campana_sms'
    model = CampanaSms

    def get_context_data(self, **kwargs):
        context = super(CampanaReporteSmsEnviadosListView, self).get_context_data(
            **kwargs)
        estadisticas_sms_enviados = EstadisticasCampanaSmsService()
        context['contactos_enviados'] = estadisticas_sms_enviados.\
            obtener_estadisticas_reporte_sms_enviados(self.kwargs['pk_campana_sms'])
        return context


class CampanaReporteSmsRecibidosRepuestaListView(ListView):
    """
    Muestra un listado de contactos a los cuales se le recibieron una repuesta
    esperada
    """
    template_name = 'reporte/detalle_reporte_sms_recibidos.html'
    context_object_name = 'campana_sms'
    model = CampanaSms

    def dispatch(self, request, *args, **kwargs):
        self.campana_sms = \
            CampanaSms.objects.obtener_tiene_repuesta_reporte(
                kwargs['pk_campana_sms'])
        return super(CampanaReporteSmsRecibidosRepuestaListView, self).dispatch(
            request, *args, **kwargs)

    def get_object(self, queryset=None):
        return CampanaSms.objects.obtener_tiene_repuesta_reporte(
            self.kwargs['pk_campana_sms'])

    def get_context_data(self, **kwargs):
        context = super(CampanaReporteSmsRecibidosRepuestaListView, self).get_context_data(
            **kwargs)
        estadisticas_sms_enviados = EstadisticasCampanaSmsService()
        context['contactos_recibidos'] = estadisticas_sms_enviados.\
            obtener_estadisticas_reporte_sms_recibido_respuesta(self.kwargs['pk_campana_sms'])
        context['campana_sms'] = self.get_object()
        return context

