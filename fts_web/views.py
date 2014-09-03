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
# Archivo Audio
# =============================================================================

class ArchivoAudioListView(ListView):
    """
    Esta vista lista los archivos de audios.
    """

    template_name = 'archivo_audio/lista_archivo_audio.html'
    context_object_name = 'audios'
    model = ArchivoDeAudio
    queryset = ArchivoDeAudio.objects.all()


class ArchivoAudioCreateView(CreateView):
    """
    Esta vista crea un objeto ArchivoDeAudio.
    """

    template_name = 'archivo_audio/nuevo_edita_archivo_audio.html'
    model = ArchivoDeAudio
    form_class = ArchivoAudioForm

    def form_valid(self, form):
        self.object = form.save()

        try:
            conversor_audio = ConversorDeAudioService()
            conversor_audio.convertir_audio_de_archivo_de_audio_globales(
                self.object)
            return redirect(self.get_success_url())

        except FtsAudioConversionError:
            self.object.audio_original = None
            self.object.save()

            message = '<strong>Operación Errónea!</strong> \
                Hubo un inconveniente en la conversión del audio. Por favor \
                verifique que el archivo subido sea el indicado.'
            messages.add_message(
                self.request,
                messages.ERROR,
                message,
            )
            return self.form_invalid(form)
        except Exception, e:
            self.object.audio_original = None
            self.object.save()

            logger.warn("convertir_audio_de_archivo_de_audio_globales(): "
                        "produjo un error inesperado. Detalle: %s", e)

            message = '<strong>Operación Errónea!</strong> \
                Se produjo un error inesperado en la conversión del audio.'
            messages.add_message(
                self.request,
                messages.ERROR,
                message,
            )
            return self.form_invalid(form)

    def get_success_url(self):
        return reverse('lista_archivo_audio')


class ArchivoAudioUpdateView(UpdateView):
    """
    Esta vista edita un objeto ArchivoDeAudio.
    """

    template_name = 'archivo_audio/nuevo_edita_archivo_audio.html'
    model = ArchivoDeAudio
    form_class = ArchivoAudioForm

    # @@@@@@@@@@@@@@@@@@@@

    def form_valid(self, form):
        self.object = form.save()

        if self.request.FILES.get('audio_original'):
            try:
                conversor_audio = ConversorDeAudioService()
                conversor_audio.convertir_audio_de_archivo_de_audio_globales(
                    self.object)
                return redirect(self.get_success_url())
            except FtsAudioConversionError:
                self.object.audio_original = None
                self.object.save()

                message = '<strong>Operación Errónea!</strong> \
                    Hubo un inconveniente en la conversión del audio. Por favor \
                    verifique que el archivo subido sea el indicado.'
                messages.add_message(
                    self.request,
                    messages.ERROR,
                    message,
                )
                return self.form_invalid(form)
            except Exception, e:
                self.object.audio_original = None
                self.object.save()

                logger.warn("convertir_audio_de_archivo_de_audio_globales(): "
                            "produjo un error inesperado. Detalle: %s", e)

                message = '<strong>Operación Errónea!</strong> \
                    Se produjo un error inesperado en la conversión del audio.'
                messages.add_message(
                    self.request,
                    messages.ERROR,
                    message,
                )
                return self.form_invalid(form)

        return redirect(self.get_success_url())

    def get_success_url(self):
        return reverse('lista_archivo_audio')


class ArchivoAudioDeleteView(DeleteView):
    """
    Esta vista se encarga de la eliminación del
    objeto ArchivoDeAudio seleccionado.
    """

    model = ArchivoDeAudio
    template_name = 'archivo_audio/elimina_archivo_audio.html'
    queryset = ArchivoDeAudio.objects.all()

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        success_url = self.get_success_url()

        # Marcamos el grupo de atención como borrado.
        self.object.borrar()

        message = '<strong>Operación Exitosa!</strong>\
        Se llevó a cabo con éxito la eliminación del Archivo de Audio.'

        messages.add_message(
            self.request,
            messages.SUCCESS,
            message,
        )
        return HttpResponseRedirect(success_url)

    def get_success_url(self):
        return reverse('lista_archivo_audio')


# =============================================================================
# Test
# =============================================================================

def test_view_exception(request):
    raise Exception("ERROR FICTICIO")
