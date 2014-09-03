# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.cache import get_cache
from django.core.urlresolvers import reverse
from django.db import transaction
from django.http import HttpResponseRedirect
from django.shortcuts import redirect, get_object_or_404
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views.generic import (
    CreateView, ListView, DeleteView, UpdateView, DetailView,
    RedirectView, TemplateView)
from fts_daemon.asterisk_config import create_dialplan_config_file, \
    reload_config, create_queue_config_file
from fts_daemon.audio_conversor import (ConversorDeAudioService)
from fts_daemon.poll_daemon.statistics import StatisticsService
from fts_daemon.tasks import esperar_y_depurar_campana_async
from fts_web import version
from fts_web.errors import (FtsAudioConversionError,
                            FtsParserCsvDelimiterError, FtsParserMinRowError,
                            FtsParserMaxRowError, FtsParserOpenFileError,
                            FtsDepuraBaseDatoContactoError)
from fts_web.forms import DerivacionExternaForm, GrupoAtencionForm, \
    AgentesGrupoAtencionFormSet, BaseDatosContactoForm, ArchivoAudioForm
from fts_web.models import (
    Campana, GrupoAtencion, DerivacionExterna,
    BaseDatosContacto, ArchivoDeAudio)
from fts_web.parser import ParserCsv
from fts_web.services.base_de_datos_contactos import CreacionBaseDatosService
from fts_web.services.estadisticas_campana import EstadisticasCampanaService
from fts_web.services.reporte_campana import ReporteCampanaService
import logging as logging_

from fts_web.views_archivo_de_audio import *
from fts_web.views_base_de_datos_contacto import *
from fts_web.views_campana import *
from fts_web.views_derivacion import *
from fts_web.views_grupo_atencion import *
from fts_web.views_campana_creacion import *
from fts_web.views_campana_reciclado import *
from fts_web.views_campana_template import *
from fts_web.views_daemon_status import *

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
# Test
# =============================================================================

def test_view_exception(request):
    raise Exception("ERROR FICTICIO")
