# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import json
import pygal

from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.views.generic import TemplateView

from fts_web.models import Campana
from fts_web.services.estadisticas_campana import ESTILO_VERDE_ROJO_NARANJA


# =============================================================================
# Nuevas vistas para los gráficos de los reportes.
# =============================================================================


class CreaGraficoDeDuracionDeLlamada(TemplateView):
    def render_to_response(self, context, **response_kwargs):

        campana = get_object_or_404(
            Campana, pk=self.kwargs['pk']
        )

        estadisticas = json.loads(campana.estadisticas)
        datos = estadisticas['duracion_de_llamadas']

        torta = pygal.Pie(legend_at_bottom=True,
                          style=ESTILO_VERDE_ROJO_NARANJA,
                          no_data_text='No se encontraron datos.',
                          no_data_font_size=32,
                          legend_font_size=25,
                          truncate_legend=10,
                          tooltip_font_size=30)

        torta.add('SI escucharon todo el mensaje.',
                  datos['si_escucharon_todo_el_mensaje'])
        torta.add('NO escucharon todo el mensaje.',
                  datos['no_escucharon_todo_el_mensaje'])

        return HttpResponse(torta.render(), content_type='image/svg+xml')
