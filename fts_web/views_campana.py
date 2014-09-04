# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from django.contrib import messages
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect
from django.shortcuts import redirect
from django.views.generic.base import RedirectView
from django.views.generic.detail import DetailView
from django.views.generic.edit import DeleteView, UpdateView
from django.views.generic.list import ListView
from fts_daemon.tasks import esperar_y_depurar_campana_async
from fts_web.models import Campana
from fts_web.services.estadisticas_campana import EstadisticasCampanaService
from fts_web.services.reporte_campana import ReporteCampanaService

import logging as logging_
from fts_web.views_daemon_status import _update_context_with_statistics


logger = logging_.getLogger(__name__)

# =============================================================================
# Campaña
# =============================================================================


class CampanaListView(ListView):
    """
    Esta vista lista los objetos Capanas
    diferenciadas por sus estados actuales.
    Pasa un diccionario al template
    con las claves como estados.
    """

    template_name = 'campana/lista_campana.html'
    context_object_name = 'campanas'
    model = Campana

    def get_context_data(self, **kwargs):
        context = super(CampanaListView, self).get_context_data(
           **kwargs)
        context['activas'] = Campana.objects.obtener_activas()
        context['pausadas'] = Campana.objects.obtener_pausadas()
        context['finalizadas'] = Campana.objects.obtener_finalizadas()
        context['depuradas'] = Campana.objects.obtener_depuradas()
        return context


class CampanaDeleteView(DeleteView):
    """
    Esta vista se encarga de la eliminación del
    objeto Campana.
    """

    model = Campana
    template_name = 'campana/elimina_campana.html'

    # @@@@@@@@@@@@@@@@@@@@

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        success_url = self.get_success_url()

        # Marcamos la campaña como borrada. Lo hacemos primero para que,
        # en caso de error, la excepcion se lance lo antes posible
        self.object.borrar()

        # Eliminamos la tabla generada en la depuración de la campaña.
        from fts_daemon.models import EventoDeContacto
        EventoDeContacto.objects.eliminar_tabla_eventos_de_contacto_depurada(
            self.object.pk)

        message = '<strong>Operación Exitosa!</strong>\
        Se llevó a cabo con éxito la eliminación de la Campaña.'

        messages.add_message(
            self.request,
            messages.SUCCESS,
            message,
        )
        return HttpResponseRedirect(success_url)

    def get_success_url(self):
        return reverse('lista_campana')


class FinalizaCampanaView(RedirectView):
    """
    Esta vista actualiza la campañana finalizándola.
    """

    pattern_name = 'lista_campana'

    # @@@@@@@@@@@@@@@@@@@@

    def post(self, request, *args, **kwargs):
        campana = Campana.objects.get(pk=request.POST['campana_id'])

        if campana.puede_finalizarse():
            campana.finalizar()
            esperar_y_depurar_campana_async(campana.id)
            message = '<strong>Operación Exitosa!</strong>\
            La campaña ha sido finalizada.'

            messages.add_message(
                self.request,
                messages.SUCCESS,
                message,
            )
        else:
            message = '<strong>Operación Errónea!</strong>\
            El estado actual de la campaña no permite su finalización.'

            messages.add_message(
                self.request,
                messages.ERROR,
                message,
            )

        return super(FinalizaCampanaView, self).post(request, *args, **kwargs)


class PausaCampanaView(RedirectView):
    """
    Esta vista actualiza la campañana pausándola.
    """

    pattern_name = 'lista_campana'

    def post(self, request, *args, **kwargs):
        campana = Campana.objects.get(pk=request.POST['campana_id'])
        campana.pausar()

        message = '<strong>Operación Exitosa!</strong>\
        Se llevó a cabo con éxito el pausado de\
        la Campaña.'

        messages.add_message(
            self.request,
            messages.SUCCESS,
            message,
        )
        return super(PausaCampanaView, self).post(request, *args, **kwargs)


class ActivaCampanaView(RedirectView):
    """
    Esta vista actualiza la campañana activándola.
    """

    pattern_name = 'lista_campana'

    def post(self, request, *args, **kwargs):
        campana = Campana.objects.get(pk=request.POST['campana_id'])
        campana.despausar()

        message = '<strong>Operación Exitosa!</strong>\
        Se llevó a cabo con éxito la activación de\
        la Campaña.'

        messages.add_message(
            self.request,
            messages.SUCCESS,
            message,
        )
        return super(ActivaCampanaView, self).post(request, *args, **kwargs)


class DetalleCampanView(DetailView):
    """
    Muestra el detalle de la campaña.
    """
    template_name = 'campana/detalle_campana.html'
    context_object_name = 'campana'
    pk_url_kwarg = 'pk_campana'
    model = Campana


class ExportaReporteCampanaView(UpdateView):
    """
    Esta vista invoca a generar un csv de reporte de la campana.
    """

    model = Campana
    context_object_name = 'campana'

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()

        service = ReporteCampanaService()
        url = service.obtener_url_reporte_csv_descargar(self.object)

        return redirect(url)


# =============================================================================
# Estados
# =============================================================================


class CampanaPorEstadoListView(ListView):
    """
    Esta vista lista los objetos Capanas
    diferenciadas por sus estados actuales.
    Pasa un diccionario al template
    con las claves como estados.
    """

    template_name = 'estado/estado.html'
    context_object_name = 'campanas'
    model = Campana

    def get_context_data(self, **kwargs):
        context = super(CampanaPorEstadoListView, self).get_context_data(
           **kwargs)

        # obtener_estadisticas_render_graficos_supervision()
        service = EstadisticasCampanaService()
        campanas_ejecucion = Campana.objects.obtener_ejecucion()
        for campana in campanas_ejecucion:
            campana.hack__graficos_estadisticas = \
                service.obtener_estadisticas_render_graficos_supervision(
                    campana)
        context['campanas_ejecucion'] = campanas_ejecucion
        _update_context_with_statistics(context)
        return context


class CampanaEstadoOpcionesDetailView(DetailView):
    """
    Muestra el estado de la campaña con la lista de
    contactos asociados, y el estado de c/u de dichos contactos
    """

    template_name = 'estado/detalle_estado_opciones.html'
    context_object_name = 'campana'
    model = Campana

    def get_context_data(self, **kwargs):
        context = super(CampanaEstadoOpcionesDetailView,
                        self).get_context_data(**kwargs)

        context['detalle_opciones'] = self.object.\
            obtener_detalle_opciones_seleccionadas()
        return context


# =============================================================================
# Reporte
# =============================================================================


class CampanaReporteListView(ListView):
    """
    Esta vista lista las campañas finalizadas con
    un resumen de sus características.
    """

    template_name = 'reporte/reporte.html'
    context_object_name = 'campana'
    model = Campana

    def get_context_data(self, **kwargs):
        context = super(CampanaReporteListView, self).get_context_data(
            **kwargs)
        context['campanas_finalizadas'] = Campana.objects.obtener_depuradas()
        return context


class CampanaReporteDetailView(DetailView):
    """
    Muestra el estado de la campaña con la lista de
    contactos asociados, y el estado de c/u de dichos contactos
    """
    template_name = 'reporte/detalle_reporte.html'
    context_object_name = 'campana'
    model = Campana

    def get_queryset(self):
        return Campana.objects.obtener_depuradas()

    def get_object(self, *args, **kwargs):
        service = EstadisticasCampanaService()

        campana = super(CampanaReporteDetailView, self).get_object(
            *args, **kwargs)

        campana.hack__graficos_estadisticas = \
            service.obtener_estadisticas_render_graficos_reportes(
                campana)

        return campana
