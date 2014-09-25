# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import json

from django.contrib import messages
from django.core.urlresolvers import reverse
from django.db import transaction
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import redirect, get_object_or_404
from django.views.generic.edit import (CreateView, UpdateView, DeleteView,
                                       BaseUpdateView)
from fts_daemon.asterisk_config import create_dialplan_config_file, \
    reload_config, create_queue_config_file
from fts_daemon.audio_conversor import convertir_audio_de_campana
from fts_web.errors import FtsAudioConversionError
from fts_web.forms import CampanaForm, AudioForm, CalificacionForm, \
    OpcionForm, ActuacionForm, ConfirmaForm, OrdenAudiosForm
from fts_web.models import Campana, ArchivoDeAudio, Calificacion, Opcion, \
    Actuacion, AudioDeCampana
from fts_web.services.audios_campana import OrdenAudiosCampanaService
import logging as logging_


logger = logging_.getLogger(__name__)


# __all__ = ["CheckEstadoCampanaMixin", "CampanaCreateView",
#            "CampanaUpdateView", "AudioCampanaCreateView",
#            "CalificacionCampanaCreateView"]

class CheckEstadoTemplateMixin(object):
    """Mixin para utilizar en las vistas de creación de campañas/template.
    Utiliza `Campana.objects_template.obtener_en_definicion_para_editar()`
    para obtener la campañas/template para obtener la campaña pasada por url.
    Este metodo falla si la campañas/template no deberia ser editada.
    ('editada' en el contexto del proceso de creacion de la campañas/template.)
    """

    def dispatch(self, request, *args, **kwargs):
        self.campana = \
            Campana.objects_template.obtener_en_definicion_para_editar(
                kwargs['pk_campana'])

        kwargs.update({'_campana_chequeada': True})

        return super(CheckEstadoTemplateMixin, self).dispatch(request, *args,
                                                              **kwargs)


class CheckEstadoCampanaMixin(object):
    """Mixin para utilizar en las vistas de creación de campañas.
    Utiliza `Campana.objects.obtener_en_definicion_para_editar()`
    para obtener la campaña pasada por url.
    Este metodo falla si la campaña no deberia ser editada.
    ('editada' en el contexto del proceso de creacion de la campaña)
    """

    def dispatch(self, request, *args, **kwargs):
        chequeada = kwargs.pop('_campana_chequeada', False)
        if not chequeada:
            self.campana = Campana.objects.obtener_en_definicion_para_editar(
                self.kwargs['pk_campana'])

        return super(CheckEstadoCampanaMixin, self).dispatch(request, *args,
                                                             **kwargs)


class TemplateEnDefinicionMixin(object):
    """Mixin para obtener el objeto campama/template que valida que siempre
    este en el estado en definición.
    """

    def get_object(self, queryset=None):
        return Campana.objects_template.obtener_en_definicion_para_editar(
            self.kwargs['pk_campana'])


class CampanaEnDefinicionMixin(object):
    """Mixin para obtener el objeto campama que valida que siempre este en
    el estado en definición.
    """

    def get_object(self, queryset=None):
        return Campana.objects.obtener_en_definicion_para_editar(
            self.kwargs['pk_campana'])


class CampanaCreateUpdateMixin(object):
    """
    Mixin para el proceso de creado y edición de las campana con el método
    post que se encarga de validar que los tts de la campana, en caso de tener,
    coinicidan con las columnas de la base de datos.
    """

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()

        form_class = self.get_form_class()
        form = self.get_form(form_class)

        if form.is_valid():
            # Por mas que el form sea válido, validamos que los tts también
            # lo son, de lo contrario, seteamos el error y llamamos a
            # form_invalid, si los tts son válidos el método sigue su curso
            # normal.
            if not self.object.valida_tts():
                form.errors.update({'bd_contacto':
                                   ['La base de datos seleccionada no tiene '
                                    'las columnas que tienen los tts de la '
                                    'campana.']})
                return self.form_invalid(form)

            return self.form_valid(form)
        else:
            return self.form_invalid(form)


class CampanaCreateView(CampanaCreateUpdateMixin, CreateView):
    """
    Esta vista crea un objeto Campana.
    Por defecto su estado es EN_DEFICNICION,
    Redirecciona a crear las opciones para esta
    Campana.
    """

    template_name = 'campana/nueva_edita_campana.html'
    model = Campana
    context_object_name = 'campana'
    form_class = CampanaForm

    def get_success_url(self):
        return reverse(
            'audio_campana',
            kwargs={"pk_campana": self.object.pk})


class CampanaUpdateView(CampanaCreateUpdateMixin, CheckEstadoCampanaMixin,
                        CampanaEnDefinicionMixin, UpdateView):
    """
    Esta vista actualiza un objeto Campana.
    """

    template_name = 'campana/nueva_edita_campana.html'
    model = Campana
    context_object_name = 'campana'
    form_class = CampanaForm

    def get_success_url(self):
        return reverse(
            'audio_campana',
            kwargs={"pk_campana": self.object.pk})


class AudioCampanaCreateView(CheckEstadoCampanaMixin, CreateView):
    """
    Esta vista actuaiza un objeto Campana
    con el upload del audio.
    """

    template_name = 'campana/audio_campana.html'
    model = AudioDeCampana
    form_class = AudioForm

    # @@@@@@@@@@@@@@@@@@@@

    def get_initial(self):
        initial = super(AudioCampanaCreateView, self).get_initial()
        initial.update({'campana': self.campana.id})
        return initial

    def get_form(self, form_class):
        nombres_de_columnas = []
        if self.campana.bd_contacto:
            metadata = self.campana.bd_contacto.get_metadata()
            nombres_de_columnas = metadata.nombres_de_columnas

        tts_choices = [(columna, columna) for columna in nombres_de_columnas]
        return form_class(tts_choices=tts_choices, **self.get_form_kwargs())

    def get_context_data(self, **kwargs):
        context = super(AudioCampanaCreateView,
                        self).get_context_data(**kwargs)
        context['campana'] = self.campana
        context['ORDEN_SENTIDO_UP'] = AudioDeCampana.ORDEN_SENTIDO_UP
        context['ORDEN_SENTIDO_DOWN'] = AudioDeCampana.ORDEN_SENTIDO_DOWN

        # FIXME: Instanciar este formulario en el GET preferentemente.
        form_orden_audios = OrdenAudiosForm()
        context['form_orden_audios'] = form_orden_audios

        return context

    def form_valid(self, form):
        archivo_de_audio = self.request.POST.get('archivo_de_audio')
        audio_original = self.request.FILES.get('audio_original')
        tts = self.request.POST.get('tts')

        if ((archivo_de_audio and audio_original)
                or (archivo_de_audio and tts)
                or (audio_original and tts)
                or (archivo_de_audio and audio_original and tts)):

            message = '<strong>Operación Errónea!</strong> \
                Puede seleccionr solo una opción para el audio de la campana.'
            messages.add_message(
                self.request,
                messages.ERROR,
                message,
            )
            return self.form_invalid(form)

        if archivo_de_audio or audio_original or tts:
            self.object = form.save(commit=False)
            self.object.orden = \
                AudioDeCampana.objects.obtener_siguiente_orden(self.campana.pk)
            self.object.save()

            if audio_original:
                try:
                    self.object.audio_descripcion = audio_original.name
                    self.object.save()

                    convertir_audio_de_campana(self.object)
                except FtsAudioConversionError:
                    self.object.delete()

                    message = '<strong>Operación Errónea!</strong> \
                        Hubo un inconveniente en la conversión del audio.\
                        Por favor verifique que el archivo subido sea el \
                        indicado.'
                    messages.add_message(
                        self.request,
                        messages.ERROR,
                        message,
                    )
                    return self.form_invalid(form)
                except Exception, e:
                    self.object.delete()

                    logger.warn("convertir_audio_de_campana(): produjo un"
                                "error inesperado. Detalle: %s", e)

                    message = '<strong>Operación Errónea!</strong> \
                        Se produjo un error inesperado en la conversión del \
                        audio.'
                    messages.add_message(
                        self.request,
                        messages.ERROR,
                        message,
                    )
                    return self.form_invalid(form)
        else:
            message = '<strong>Operación Errónea!</strong> \
                       Debe seleccionar un archivo de Audio para la campaña.'
            messages.add_message(
                self.request,
                messages.ERROR,
                message,
            )
            return self.form_invalid(form)

        return redirect(self.get_success_url())

    def get_success_url(self):
        return reverse(
            'audio_campana',
            kwargs={"pk_campana": self.campana.pk})


class AudioCampanaOrdenView(CheckEstadoCampanaMixin, BaseUpdateView):
    """
    Esta vista actualiza el orden de los audios de campana.
    """

    model = AudioDeCampana

    def get_initial(self):
        initial = super(AudioCampanaOrdenView, self).get_initial()
        initial.update({'campana': self.campana.id})
        return initial

    def get(self, request, *args, **kwargs):
        return self.redirecciona_a_audios_campana()

    def form_valid(self, form_orden_audios):
        sentido_orden = int(form_orden_audios.cleaned_data.get(
                            'sentido_orden'))

        orden_audios_campana_service = OrdenAudiosCampanaService()
        if sentido_orden == AudioDeCampana.ORDEN_SENTIDO_UP:
            orden_audios_campana_service.baja_audio_una_posicion(
                self.get_object())
        elif sentido_orden == AudioDeCampana.ORDEN_SENTIDO_DOWN:
            orden_audios_campana_service.sube_audio_una_posicion(
                self.get_object())
        else:
            return form_invalid(form_orden_audios)

        message = '<strong>Operación Exitosa!</strong> \
                   Se llevó a cabo con éxito el reordenamiento de los audios.'
        messages.add_message(
            self.request,
            messages.SUCCESS,
            message,
        )
        return self.redirecciona_a_audios_campana()

    def form_invalid(self, form_orden_audios):
        message = '<strong>Operación Errónea!</strong> \
                   No se pudo llevar a cabo el reordenamiento de los audios.'
        messages.add_message(
            self.request,
            messages.ERROR,
            message,
        )
        return self.redirecciona_a_audios_campana()

    def post(self, request, *args, **kwargs):

        form_orden_audios = OrdenAudiosForm(request.POST)

        if form_orden_audios.is_valid():
            return self.form_valid(form_orden_audios)
        else:
            return self.form_invalid(form_orden_audios)

    def redirecciona_a_audios_campana(self):
        url = reverse('audio_campana', kwargs={"pk_campana": self.campana.pk})
        return HttpResponseRedirect(url)


class AudiosCampanaDeleteView(CheckEstadoCampanaMixin, DeleteView):
    """
    Esta vista se encarga de la eliminación del
    objeto AudioDeCampana seleccionado.
    """

    model = AudioDeCampana
    template_name = 'campana/elimina_audio_campana.html'

    # @@@@@@@@@@@@@@@@@@@@

    def delete(self, request, *args, **kwargs):
        message = '<strong>Operación Exitosa!</strong>\
            Se llevó a cabo con éxito la eliminación del Audio.'

        messages.add_message(
            self.request,
            messages.SUCCESS,
            message,
        )
        return super(AudiosCampanaDeleteView, self).delete(request, *args,
                                                           **kwargs)

    def get_success_url(self):
        return reverse('audio_campana',
                       kwargs={"pk_campana": self.campana.pk})


class CalificacionCampanaCreateView(CheckEstadoCampanaMixin, CreateView):
    """
    Esta vista crea uno o varios objetos Calificación
    para la Campana que se este creando.
    Inicializa el form con campo campana (hidden)
    con el id de campana que viene en la url.
    """

    # @@@@@@@@@@@@@@@@@@@@

    template_name = 'campana/calificacion_campana.html'
    model = Calificacion
    context_object_name = 'calificacion'
    form_class = CalificacionForm

    def get_initial(self):
        initial = super(CalificacionCampanaCreateView, self).get_initial()
        initial.update({'campana': self.campana.id})
        return initial

    def get_context_data(self, **kwargs):
        context = super(CalificacionCampanaCreateView,
                        self).get_context_data(**kwargs)
        context['campana'] = self.campana

        return context

    def get_success_url(self):
        return reverse(
            'calificacion_campana',
            kwargs={"pk_campana": self.kwargs['pk_campana']}
        )


class CalificacionCampanaDeleteView(CheckEstadoCampanaMixin, DeleteView):
    """
    Esta vista se encarga de la eliminación del
    objeto Calificación seleccionado.
    """

    model = Calificacion
    template_name = 'campana/elimina_calificacion_campana.html'

    # @@@@@@@@@@@@@@@@@@@@

    def get_object(self, queryset=None):
        # FIXME: Esté método no hace nada, se podría remover.
        calificacion = super(CalificacionCampanaDeleteView, self).get_object(
            queryset=None)
        return calificacion

    def delete(self, request, *args, **kwargs):
        message = '<strong>Operación Exitosa!</strong>\
            Se llevó a cabo con éxito la eliminación de la Calificación.'

        messages.add_message(
            self.request,
            messages.SUCCESS,
            message,
        )
        return super(CalificacionCampanaDeleteView, self).delete(request,
                                                                 *args,
                                                                 **kwargs)

    def get_success_url(self):
        return reverse('calificacion_campana',
                       kwargs={"pk_campana": self.campana.pk})


class OpcionCampanaCreateView(CheckEstadoCampanaMixin, CreateView):
    """
    Esta vista crea uno o varios objetos Opcion
    para la Campana que se este creando.
    Inicializa el form con campo campana (hidden)
    con el id de campana que viene en la url.
    """

    template_name = 'campana/opciones_campana.html'
    model = Opcion
    context_object_name = 'opcion'
    form_class = OpcionForm

    # @@@@@@@@@@@@@@@@@@@@

    def get_initial(self):
        initial = super(OpcionCampanaCreateView, self).get_initial()
        initial.update({'campana': self.campana.id})
        return initial

    def get_context_data(self, **kwargs):
        context = super(
            OpcionCampanaCreateView, self).get_context_data(**kwargs)
        context['campana'] = self.campana
        return context

    def get_success_url(self):
        return reverse(
            'opcion_campana',
            kwargs={"pk_campana": self.kwargs['pk_campana']}
        )


class OpcionCampanaDeleteView(CheckEstadoCampanaMixin, DeleteView):
    """
    Esta vista se encarga de la eliminación del
    objeto Opciión seleccionado.
    """

    model = Opcion
    template_name = 'campana/elimina_opcion_campana.html'

    # @@@@@@@@@@@@@@@@@@@@

    def get_object(self, queryset=None):
        # FIXME: Esté método no hace nada, se podría remover.
        opcion = super(OpcionCampanaDeleteView, self).get_object(
            queryset=None)
        return opcion

    def delete(self, request, *args, **kwargs):
        message = '<strong>Operación Exitosa!</strong>\
            Se llevó a cabo con éxito la eliminación de la Opción.'

        messages.add_message(
            self.request,
            messages.SUCCESS,
            message,
        )
        return super(OpcionCampanaDeleteView, self).delete(request,
                                                           *args, **kwargs)

    def get_success_url(self):
        return reverse(
            'opcion_campana',
            kwargs={"pk_campana": self.campana.pk}
        )


class ActuacionCampanaCreateView(CheckEstadoCampanaMixin, CreateView):
    """
    Esta vista crea uno o varios objetos Actuacion
    para la Campana que se este creando.
    Inicializa el form con campo campana (hidden)
    con el id de campana que viene en la url.
    """

    template_name = 'campana/actuacion_campana.html'
    model = Actuacion
    context_object_name = 'actuacion'
    form_class = ActuacionForm

    # @@@@@@@@@@@@@@@@@@@@

    def get_initial(self):
        initial = super(ActuacionCampanaCreateView, self).get_initial()
        initial.update({'campana': self.campana.id})
        return initial

    def get_context_data(self, **kwargs):
        context = super(
            ActuacionCampanaCreateView, self).get_context_data(**kwargs)
        context['campana'] = self.campana
        context['actuaciones_validas'] = \
            self.campana.obtener_actuaciones_validas()
        return context

    def form_valid(self, form):
        form_valid = super(ActuacionCampanaCreateView, self).form_valid(form)

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
            'actuacion_campana',
            kwargs={"pk_campana": self.kwargs['pk_campana']}
        )


class ActuacionCampanaDeleteView(CheckEstadoCampanaMixin, DeleteView):
    """
    Esta vista se encarga de la eliminación del
    objeto Actuación seleccionado.
    """

    model = Actuacion
    template_name = 'campana/elimina_actuacion_campana.html'

    # @@@@@@@@@@@@@@@@@@@@

    def get_object(self, queryset=None):
        # FIXME: Esté método no hace nada, se podría remover.
        actuacion = super(ActuacionCampanaDeleteView, self).get_object(
            queryset=None)
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
            'actuacion_campana',
            kwargs={"pk_campana": self.campana.pk}
        )


class ConfirmaCampanaMixin(CheckEstadoCampanaMixin, CampanaEnDefinicionMixin,
                           UpdateView):

    """
    Esta vista confirma la creación de un objeto
    Campana. Imprime el resumen del objeto y si
    es aceptado, cambia el estado del objeto a ACTIVA.
    Si el objeto ya esta ACTIVA, redirecciona
    al listado.
    """

    # @@@@@@@@@@@@@@@@@@@@

    model = Campana
    context_object_name = 'campana'
    form_class = ConfirmaForm

    def form_valid(self, form):
        if 'confirma' in self.request.POST:
            campana = self.object

            if not campana.valida_tts():
                message = '<strong>Operación Errónea!</strong> \
                    Las columnas de la base de datos seleccionado en el \
                    proceso de creación de la campana no coincide con los \
                    tts creado en audios de campana. Debe seleccionar una \
                    una base de datos válida.'
                messages.add_message(
                    self.request,
                    messages.ERROR,
                    message,
                )
                return self.form_invalid(form)

            if not campana.valida_grupo_atencion():
                message = '<strong>Operación Errónea!</strong> \
                    EL Grupo Atención seleccionado en el proceso de creación \
                    de la campana ha sido eliminado. Debe seleccionar uno \
                    válido.'
                messages.add_message(
                    self.request,
                    messages.ERROR,
                    message,
                )
                return self.form_invalid(form)

            if not campana.valida_derivacion_externa():
                message = '<strong>Operación Errónea!</strong> \
                    La Derivación Externa seleccionado en el proceso de \
                    creación de la campana ha sido eliminada. Debe \
                    seleccionar uno válido.'
                messages.add_message(
                    self.request,
                    messages.ERROR,
                    message,
                )
                return self.form_invalid(form)

            if campana.bd_contacto.verifica_depurada():
                message = """<strong>Operación Errónea!</strong>.
                No se pudo realizar la confirmación de la campaña debido a
                que durante el proceso de creación de la misma, la base de
                datos seleccionada fue depurada y no está disponible para su
                uso. Debe seleccionar una base de datos válida."""
                messages.add_message(
                    self.request,
                    messages.ERROR,
                    message,
                )
                return self.form_invalid(form)

            post_proceso_ok = True
            message = ''

            with transaction.atomic(savepoint=False):

                campana.activar()

                try:
                    create_dialplan_config_file()
                except:
                    logger.exception("ConfirmaCampanaMixin: error al intentar "
                                     "create_dialplan_config_file()")
                    post_proceso_ok = False
                    message += ' Atencion: hubo un inconveniente al generar\
                        la configuracion de Asterisk (dialplan).'

                try:
                    # Esto es algo redundante! Para que re-crear los queues?
                    # Total, esto lo hace GrupoDeAtencion!
                    create_queue_config_file()
                except:
                    logger.exception("ConfirmaCampanaMixin: error al intentar "
                                     "create_queue_config_file()")
                    post_proceso_ok = False
                    message += ' Atencion: hubo un inconveniente al generar\
                        la configuracion de Asterisk (queues).'

                try:
                    ret = reload_config()
                    if ret != 0:
                        post_proceso_ok = False
                        message += "Atencion: hubo un inconveniente al \
                            intentar recargar la configuracion de Asterisk."
                except:
                    logger.exception("ConfirmaCampanaMixin: error al intentar "
                                     "reload_config()")
                    post_proceso_ok = False
                    message += ' Atencion: hubo un inconveniente al intentar\
                        recargar la configuracion de Asterisk.'

            if post_proceso_ok:
                message = '<strong>Operación Exitosa!</strong> \
                    Se llevó a cabo con éxito la creación de \
                    la Campaña.'
                messages.add_message(
                    self.request,
                    messages.SUCCESS,
                    message,
                )
            else:
                message += ' La campaña será pausada. Por favor, contactese \
                    con el administrador del sistema.'
                messages.add_message(
                    self.request,
                    messages.WARNING,
                    message
                )
                campana.pausar()

            return redirect(self.get_success_url())

        elif 'cancela' in self.request.POST:
            pass
            # TODO: Implementar la cancelación.

    def get_success_url(self):
        return reverse('lista_campana')


class ConfirmaCampanaView(ConfirmaCampanaMixin):
    template_name = 'campana/confirma_campana.html'

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
                reverse('audio_campana', kwargs={"pk_campana": campana.pk}))

        return super(ConfirmaCampanaView, self).get(request, *args, **kwargs)

    # @@@@@@@@@@@@@@@@@@@@
