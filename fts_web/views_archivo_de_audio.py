# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from django.contrib import messages
from django.core.urlresolvers import reverse
from django.http.response import HttpResponseRedirect
from django.shortcuts import redirect
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.views.generic.list import ListView
from fts_daemon.audio_conversor import ConversorDeAudioService
from fts_web.errors import FtsAudioConversionError
from fts_web.forms import ArchivoAudioForm
from fts_web.models import ArchivoDeAudio
import logging as logging_


logger = logging_.getLogger(__name__)


class ArchivoAudioListView(ListView):
    """
    Esta vista lista los archivos de audios.
    """

    template_name = 'archivo_audio/lista_archivo_audio_fts.html'
    context_object_name = 'audios'
    model = ArchivoDeAudio
    queryset = ArchivoDeAudio.objects.all()


class ArchivoAudioCreateView(CreateView):
    """
    Esta vista crea un objeto ArchivoDeAudio.
    """

    template_name = 'archivo_audio/nuevo_edita_archivo_audio_fts.html'
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
        return reverse('lista_archivo_audio_fts')


class ArchivoAudioUpdateView(UpdateView):
    """
    Esta vista edita un objeto ArchivoDeAudio.
    """

    template_name = 'archivo_audio/nuevo_edita_archivo_audio_fts.html'
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
        return reverse('lista_archivo_audio_fts')


class ArchivoAudioDeleteView(DeleteView):
    """
    Esta vista se encarga de la eliminación del
    objeto ArchivoDeAudio seleccionado.
    """

    model = ArchivoDeAudio
    template_name = 'archivo_audio/elimina_archivo_audio_fts.html'
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
        return reverse('lista_archivo_audio_fts')
