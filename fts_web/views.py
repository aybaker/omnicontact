# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from django.views.generic import FormView

from fts_web import version
from fts_web.views_archivo_de_audio import *  # @UnusedWildImport
from fts_web.views_base_de_datos_contacto import *  # @UnusedWildImport
from fts_web.views_campana import *  # @UnusedWildImport
from fts_web.views_campana_creacion import *  # @UnusedWildImport
from fts_web.views_campana_reciclado import *  # @UnusedWildImport
from fts_web.views_campana_template import *  # @UnusedWildImport
from fts_web.views_campana_reportes import *  # @UnusedWildImport
from fts_web.views_daemon_status import *  # @UnusedWildImport
from fts_web.views_derivacion import *  # @UnusedWildImport
from fts_web.views_grupo_atencion import *  # @UnusedWildImport

from fts_web.forms import BusquedaDeLlamadasForm
from fts_web.services.busqueda_de_llamadas_de_numero_de_telefono import (
    BusquedaDeLlamadasService, NumeroDeTelefonoInvalidoError)

import logging as logging_


logger = logging_.getLogger(__name__)


# =============================================================================
# Acerca
# =============================================================================


class AcercaTemplateView(TemplateView):
    """
    Esta vista es para generar el Acerca de la app.
    """

    template_name = 'acerca/acerca.html'
    context_object_name = 'acerca'

    def get_context_data(self, **kwargs):
        context = super(
            AcercaTemplateView, self).get_context_data(**kwargs)

        # TODO: Implementar la manera que se obtienen los datos de acerca.
        context['branch'] = version.FTSENDER_BRANCH
        context['commit'] = version.FTSENDER_COMMIT
        context['fecha_deploy'] = version.FTSENDER_BUILD_DATE
        return context


# =============================================================================
# Búsqueda de Llamadas
# =============================================================================

class BusquedaDeLlamadasView(FormView):
    """
    Esta vista se encarga listar las llamadas de un número telefónico.
    """

    form_class = BusquedaDeLlamadasForm
    template_name = 'busqueda_llamadas/busqueda_llamadas.html'

    def form_valid(self, form):
        """
        Instacia el servicio de reporte de telefono para obtener el detalle
        de las llamadas del número ingresado.
        Se pasa al template un DTO con el detalle de la búsqueda.
        """
        numero_telefono = form.cleaned_data.get('numero_telefono')

        busqueda_de_llamadas_service = BusquedaDeLlamadasService()
        try:
            listado_de_llamadas = busqueda_de_llamadas_service.buscar_llamadas(
                numero_telefono)
        except NumeroDeTelefonoInvalidoError:
            message = '<strong>Operación Errónea!</strong> \
                El número de teléfono ingresado no es válido.'
            messages.add_message(
                self.request,
                messages.ERROR,
                message,
            )
            return self.render_to_response(self.get_context_data(
                form=form, sin_resultado=True))

        if listado_de_llamadas:
            return self.render_to_response(self.get_context_data(
                form=form, listado_de_llamadas=listado_de_llamadas))

        return self.render_to_response(self.get_context_data(
            form=form, sin_resultado=True))


# =============================================================================
# Test
# =============================================================================

def test_view_exception(request):
    raise Exception("ERROR FICTICIO")
