# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from django.contrib import messages
from django.core.urlresolvers import reverse
from django.db import transaction
from django.http import HttpResponseRedirect
from django.shortcuts import redirect, get_object_or_404
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from fts_daemon.asterisk_config import create_dialplan_config_file, \
    reload_config, create_queue_config_file
from fts_daemon.audio_conversor import convertir_audio_de_campana
from fts_web.errors import FtsAudioConversionError
from fts_web.forms import CampanaForm, AudioForm, CalificacionForm, \
    OpcionForm, ActuacionForm, ConfirmaForm
from fts_web.models import Campana, ArchivoDeAudio, Calificacion, Opcion, \
    Actuacion
import logging as logging_


logger = logging_.getLogger(__name__)


# __all__ = ["CampanaEnCreacionMixin", "CampanaCreateView", "CampanaUpdateView",
#            "AudioCampanaCreateView", "CalificacionCampanaCreateView"]


class CampanaEnCreacionMixin(object):
    """Mixin para utilizar en las vistas de creación de campañas.
    Utiliza `Campana.objects.obtener_en_definicion_para_editar()`
    para obtener la campaña.
    Este metodo falla si la campaña no deberia ser editada.
    ('editada' en el contexto del proceso de creacion de la campaña)
    """

    def dispatch(self, request, *args, **kwargs):
        Campana.objects.obtener_en_definicion_para_editar(
            self.kwargs['pk_campana'])

        return super(CampanaEnCreacionMixin, self).dispatch(request, *args,
                                                            **kwargs)


class CampanaEnDefinicionMixin(object):
    """Mixin para obtener el objeto campama que valida que siempre este en
    el estado en definición.
    """

    def get_object(self, queryset=None):
        return Campana.objects.obtener_en_definicion_para_editar(
            self.kwargs['pk_campana'])


class CampanaCreateView(CreateView):
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


class CampanaUpdateView(CampanaEnCreacionMixin, CampanaEnDefinicionMixin,
                        UpdateView):
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


class AudioCampanaCreateView(CampanaEnCreacionMixin, CampanaEnDefinicionMixin,
                             UpdateView):
    """
    Esta vista actuaiza un objeto Campana
    con el upload del audio.
    """

    template_name = 'campana/audio_campana.html'
    model = Campana
    context_object_name = 'campana'
    form_class = AudioForm

    # @@@@@@@@@@@@@@@@@@@@

    def get_form(self, form_class):
        id_archivo_audio = self.object.obtener_id_archivo_audio()

        return form_class(id_archivo_audio=id_archivo_audio,
                          **self.get_form_kwargs())

    def form_valid(self, form):
        archivo_audio = self.request.POST.get('archivo_audio')
        audio_original = self.request.FILES.get('audio_original')

        if archivo_audio and audio_original:
            message = '<strong>Operación Errónea!</strong> \
                Seleccione solo un audio para la campana.'
            messages.add_message(
                self.request,
                messages.ERROR,
                message,
            )
            return redirect(self.get_success_url())

        if archivo_audio:
            archivo_audio = get_object_or_404(
                ArchivoDeAudio, pk=self.request.POST.get('archivo_audio')
            )
            self.object.audio_original = archivo_audio.audio_original
            self.object.audio_asterisk = archivo_audio.audio_asterisk
            self.object.save()

            return redirect(self.get_success_url())

        elif audio_original:
            self.object = form.save()

            try:
                convertir_audio_de_campana(self.object)
                return redirect(self.get_success_url())
            except FtsAudioConversionError:
                self.object.audio_original = None
                self.object.save()

                message = '<strong>Operación Errónea!</strong> \
                    Hubo un inconveniente en la conversión del audio.\
                    Por favor verifique que el archivo subido sea el indicado.'
                messages.add_message(
                    self.request,
                    messages.ERROR,
                    message,
                )
                return self.form_invalid(form)
            except Exception, e:
                self.object.audio_original = None
                self.object.save()

                logger.warn("convertir_audio_de_campana(): produjo un error "
                            "inesperado. Detalle: %s", e)

                message = '<strong>Operación Errónea!</strong> \
                    Se produjo un error inesperado en la conversión del audio.'
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

    def get_success_url(self):
        return reverse(
            'audio_campana',
            kwargs={"pk_campana": self.object.pk})


class CalificacionCampanaCreateView(CampanaEnCreacionMixin, CreateView):
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

        campana = Campana.objects.obtener_en_definicion_para_editar(
            self.kwargs['pk_campana'])
        initial.update({'campana': campana.id})
        return initial

    def get_context_data(self, **kwargs):
        context = super(CalificacionCampanaCreateView,
                        self).get_context_data(**kwargs)

        context['campana'] = Campana.objects.obtener_en_definicion_para_editar(
            self.kwargs['pk_campana'])

        return context

    def get_success_url(self):
        return reverse(
            'calificacion_campana',
            kwargs={"pk_campana": self.kwargs['pk_campana']}
        )


class CalificacionCampanaDeleteView(DeleteView):
    """
    Esta vista se encarga de la eliminación del
    objeto Calificación seleccionado.
    """

    model = Calificacion
    template_name = 'campana/elimina_calificacion_campana.html'

    # @@@@@@@@@@@@@@@@@@@@

    def get_object(self, queryset=None):
        calificacion = super(CalificacionCampanaDeleteView, self).get_object(
            queryset=None)

        # De alguna manera hay q' validar la campaña! Pero esta CBV entra
        # por el ID de calificacion, asi q' bueno, lo sigueinte queda
        # raro, pero hace falta!
        self.campana = Campana.objects.obtener_en_definicion_para_editar(
            calificacion.campana.id)

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
        return reverse(
            'calificacion_campana',
            kwargs={"pk": self.campana.pk}
        )


class OpcionCampanaCreateView(CampanaEnCreacionMixin, CreateView):
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
        campana = Campana.objects.obtener_en_definicion_para_editar(
            self.kwargs['pk_campana'])
        initial.update({'campana': campana.id})
        return initial

    def get_context_data(self, **kwargs):
        context = super(
            OpcionCampanaCreateView, self).get_context_data(**kwargs)

        context['campana'] = Campana.objects.obtener_en_definicion_para_editar(
            self.kwargs['pk_campana'])
        return context

    def get_success_url(self):
        return reverse(
            'opcion_campana',
            kwargs={"pk_campana": self.kwargs['pk_campana']}
        )


class OpcionCampanaDeleteView(DeleteView):
    """
    Esta vista se encarga de la eliminación del
    objeto Opciión seleccionado.
    """

    model = Opcion
    template_name = 'campana/elimina_opcion_campana.html'

    # @@@@@@@@@@@@@@@@@@@@

    def get_object(self, queryset=None):
        opcion = super(OpcionCampanaDeleteView, self).get_object(
            queryset=None)

        # De alguna manera hay q' validar la campaña! Pero esta CBV entra
        # por el ID de calificacion, asi q' bueno, lo sigueinte queda
        # raro, pero hace falta!
        self.campana = Campana.objects.obtener_en_definicion_para_editar(
            opcion.campana.id)

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
            kwargs={"pk": self.campana.pk}
        )


class ActuacionCampanaCreateView(CampanaEnCreacionMixin, CreateView):
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
        campana = Campana.objects.obtener_en_definicion_para_editar(
            self.kwargs['pk_campana'])
        initial.update({'campana': campana.id})
        return initial

    def get_context_data(self, **kwargs):
        context = super(
            ActuacionCampanaCreateView, self).get_context_data(**kwargs)

        campana = Campana.objects.obtener_en_definicion_para_editar(
            self.kwargs['pk_campana'])

        context['campana'] = campana
        context['actuaciones_validas'] = campana.obtener_actuaciones_validas()
        return context

    def form_valid(self, form):
        form_valid = super(ActuacionCampanaCreateView, self).form_valid(form)

        campana = Campana.objects.obtener_en_definicion_para_editar(
            self.kwargs['pk_campana'])

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

        return form_valid

    def get_success_url(self):
        return reverse(
            'actuacion_campana',
            kwargs={"pk_campana": self.kwargs['pk_campana']}
        )


class ActuacionCampanaDeleteView(DeleteView):
    """
    Esta vista se encarga de la eliminación del
    objeto Actuación seleccionado.
    """

    model = Actuacion
    template_name = 'campana/elimina_actuacion_campana.html'

    # @@@@@@@@@@@@@@@@@@@@

    def get_object(self, queryset=None):
        actuacion = super(ActuacionCampanaDeleteView, self).get_object(
            queryset=None)

        # De alguna manera hay q' validar la campaña! Pero esta CBV entra
        # por el ID de calificacion, asi q' bueno, lo sigueinte queda
        # raro, pero hace falta!
        self.campana = Campana.objects.obtener_en_definicion_para_editar(
            actuacion.campana.id)
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
            kwargs={"pk": self.campana.pk}
        )


class ConfirmaCampanaMixin(CampanaEnCreacionMixin, CampanaEnDefinicionMixin,
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
                # TODO: Cuando en el proceso de creación de la campana se
                # pueda ir volviendo de paso, mostrar el error y no
                # redireccionar, permitir que puda seleccionar otra base de
                # datos.

                message = """<strong>Operación Errónea!</strong>.
                No se pudo realizar la confirmación de la campaña debido a
                que durante el proceso de creación de la misma, la base de
                datos seleccionada fue depurada y no está disponible para su
                uso. La campaña no se creará."""
                messages.add_message(
                    self.request,
                    messages.ERROR,
                    message,
                )
                return redirect(self.get_success_url())

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
