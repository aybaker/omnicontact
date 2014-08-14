# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from django.conf import settings
from django.contrib import messages
from django.core.cache import get_cache
from django.core.urlresolvers import reverse
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.db import transaction
from django.http import HttpResponseRedirect
from django.shortcuts import redirect, get_object_or_404
from django.utils import timezone
from django.views.generic.list import BaseListView
from django.views.generic import (
    CreateView, ListView, DeleteView, FormView, UpdateView, DetailView,
    RedirectView, TemplateView)
from fts_daemon.asterisk_config import create_dialplan_config_file, \
    reload_config, create_queue_config_file
from fts_daemon.audio_conversor import (convertir_audio_de_campana,
    convertir_audio_de_archivo_de_audio_globales)
from fts_daemon.poll_daemon.statistics import StatisticsService
from fts_daemon.tasks import esperar_y_depurar_campana_async
from fts_web.errors import (FtsAudioConversionError,
    FtsParserCsvDelimiterError, FtsParserMinRowError, FtsParserMaxRowError,
    FtsParserOpenFileError, FtsRecicladoCampanaError,
    FtsDepuraBaseDatoContactoError)
from fts_web.forms import (
    ActuacionForm, AgentesGrupoAtencionFormSet, AudioForm, CampanaForm,
    CalificacionForm, ConfirmaForm, GrupoAtencionForm, TipoRecicladoForm,
    BaseDatosContactoForm, OpcionForm, DerivacionExternaForm, TemplateForm,
    ArchivoAudioForm)
from fts_web.models import (
    Actuacion, Calificacion, Campana, GrupoAtencion, DerivacionExterna,
    BaseDatosContacto, Opcion, ArchivoDeAudio)
from fts_web.parser import autodetectar_parser
import logging as logging_
from fts_web.reciclador_base_datos_contacto.reciclador import (
    RecicladorBaseDatosContacto, CampanaEstadoInvalidoError,
    CampanaTipoRecicladoInvalidoError)
from fts_web import version


logger = logging_.getLogger(__name__)


# ==============================================================================
# Acerca
# ==============================================================================


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


# ==============================================================================
# Derivación
# ==============================================================================


class DerivacionListView(ListView):
    """
    Esta vista es para generar el listado de
    GrupoAtencion y Derivaciones Externas.
    """

    template_name = 'derivacion/lista_derivacion.html'
    queryset = []

    def get_context_data(self, **kwargs):
        context = super(
            DerivacionListView, self).get_context_data(**kwargs)

        context['grupos_atencion'] = GrupoAtencion.objects.all()
        context['derivaciones_externa'] = DerivacionExterna.objects.all()
        return context


class DerivacionExternaMixin(object):
    """
    Mixin para DerivacionExterna
    """

    def crea_y_recarga_dialplan(self):
        """
        Este método se encarga de invocar rehacer el dialplan y recargar el
        mismo.
        """
        try:
            create_dialplan_config_file()
        except:
            logger.exception("DerivacionExternaMixin: error al intentar "
                             "create_dialplan_config_file()")
            post_proceso_ok = False

            messages.add_message(
                self.request,
                messages.ERROR,
                "Atencion: hubo un inconveniente al generar "
                "la configuracion de Asterisk (dialplan). "
            )

        try:
            ret = reload_config()
            if ret != 0:
                messages.add_message(
                    self.request,
                    messages.ERROR,
                    "Atencion: hubo un inconveniente al intentar "
                    "recargar la configuracion de Asterisk. "
                    "Por favor, contáctese con el administrador "
                    "del sistema."
                )
        except:
            logger.exception("DerivacionExternaMixin: error al intentar "
                             "reload_config()")
            messages.add_message(
                self.request,
                messages.ERROR,
                "Atencion: hubo un inconveniente al intentar "
                "recargar la configuracion de Asterisk. "
                "Por favor, contáctese con el administrador "
                "del sistema."
            )


class DerivacionExternaCreateView(CreateView):
    """
    Esta vista crea un objeto DerivaciónExterna.
    """

    template_name = 'derivacion/derivacion_externa.html'
    model = DerivacionExterna
    context_object_name = 'derivacion_externa'
    form_class = DerivacionExternaForm

    def form_valid(self, form):

        message = '<strong>Operación Exitosa!</strong>\
                Se llevó a cabo con éxito la creación de Derivación Externa.'

        messages.add_message(
            self.request,
            messages.SUCCESS,
            message,
        )
        return super(DerivacionExternaCreateView, self).form_valid(form)

    def get_success_url(self):
        return reverse('lista_derivacion')


class DerivacionExternaUpdateView(UpdateView, DerivacionExternaMixin):
    """
    Esta vista edita un objeto DerivaciónExterna.
    """
    template_name = 'derivacion/derivacion_externa.html'
    model = DerivacionExterna
    context_object_name = 'derivacion_externa'
    form_class = DerivacionExternaForm

    def form_valid(self, form):
        self.object = form.save()

        message = '<strong>Operación Exitosa!</strong>\
                Se llevó a cabo con éxito la modificación de Derivación\
                Externa.'

        messages.add_message(
            self.request,
            messages.SUCCESS,
            message,
        )

        self.crea_y_recarga_dialplan()

        return HttpResponseRedirect(self.get_success_url())

    def get_success_url(self):
        return reverse('lista_derivacion')


class DerivacionExternaDeleteView(DeleteView):
    """
    Esta vista se encarga de la eliminación del
    objeto DerivaciónExterna seleccionado.
    """

    model = DerivacionExterna
    template_name = 'derivacion/elimina_derivacion_externa.html'
    queryset = DerivacionExterna.objects.all()

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        success_url = self.get_success_url()

        # Marcamos el grupo de atención como borrado.
        self.object.borrar()

        message = '<strong>Operación Exitosa!</strong>\
        Se llevó a cabo con éxito la eliminación de la Derivación Externa.'

        messages.add_message(
            self.request,
            messages.SUCCESS,
            message,
        )
        return HttpResponseRedirect(success_url)

    def get_success_url(self):
        return reverse('lista_derivacion')


class GrupoAtencionMixin(object):
    """
    Este mixin procesa y valida
    los formularios en la creación y edición
    de objetos GrupoAtencion.
    """

    @transaction.atomic(savepoint=False)
    def process_all_forms_in_tx(self, form, update=False):
        """
        Este método se encarga de validar el
        formularios GrupoAtencionForm y hacer
        el save. Luego instancia el formset
        AgentesGrupoAtencionFormSet con el
        objeto creado y si es válido realiza
        el save.
        """

        if form.is_valid():
            self.object = form.save()

        formset_agente_grupo_atencion = self.formset_agente_grupo_atencion(
            self.request.POST, instance=self.object)

        is_valid = all([
            form.is_valid(),
            formset_agente_grupo_atencion.is_valid(),
        ])

        if is_valid:
            formset_agente_grupo_atencion.save()

            message = '<strong>Operación Exitosa!</strong>\
            Se llevó a cabo con éxito la operación.'

            messages.add_message(
                self.request,
                messages.SUCCESS,
                message,
            )

            try:
                create_queue_config_file()
            except:
                logger.exception("GrupoAtencionMixin: error al intentar "
                    "create_queue_config_file()")
                messages.add_message(
                    self.request,
                    messages.ERROR,
                    "Atencion: hubo un inconveniente al generar "
                    "la configuracion de Asterisk (queues). "
                    "Por favor, contáctese con el administrador "
                    "del sistema."
                )

            try:
                ret = reload_config()
                if ret != 0:
                    messages.add_message(
                        self.request,
                        messages.ERROR,
                        "Atencion: hubo un inconveniente al intentar "
                        "recargar la configuracion de Asterisk. "
                        "Por favor, contáctese con el administrador "
                        "del sistema."
                    )
            except:
                logger.exception("GrupoAtencionMixin: error al intentar "
                    "reload_config()")
                messages.add_message(
                    self.request,
                    messages.ERROR,
                    "Atencion: hubo un inconveniente al intentar "
                    "recargar la configuracion de Asterisk. "
                    "Por favor, contáctese con el administrador "
                    "del sistema."
                )

            return redirect(self.get_success_url())
        else:
            if form.is_valid() and not update:
                self.object.delete()
                self.object = None

            messages.add_message(
                self.request,
                messages.ERROR,
                '<strong>Operación Errónea!</strong>\
                Revise y complete todos los campos obligatorios\
                para la creación de una nuevo Grupo de Atención.',
            )
            context = self.get_context_data(
                form=form,
                formset_agente_grupo_atencion=formset_agente_grupo_atencion,
            )

            return self.render_to_response(context)


class GrupoAtencionCreateView(CreateView, GrupoAtencionMixin):
    """
    Esta vista crea un objeto GrupoAtencion.
    """

    template_name = 'derivacion/grupo_atencion.html'
    model = GrupoAtencion
    context_object_name = 'grupo_atencion'
    form_class = GrupoAtencionForm
    formset_agente_grupo_atencion = AgentesGrupoAtencionFormSet

    def get_context_data(self, **kwargs):
        context = super(
            GrupoAtencionCreateView, self).get_context_data(**kwargs)

        if 'formset_agente_grupo_atencion' not in context:
            context['formset_agente_grupo_atencion'] = \
            self.formset_agente_grupo_atencion(
                instance=self.object
            )
        return context

    def form_valid(self, form):
        return self.process_all_forms_in_tx(form)

    def form_invalid(self, form):
        return self.process_all_forms_in_tx(form)

    def get_success_url(self):
        return reverse('lista_derivacion')


class GrupoAtencionUpdateView(UpdateView, GrupoAtencionMixin):
    """
    Esta vista actualiza el objeto GrupoAtencion
    seleccionado.
    """

    template_name = 'derivacion/grupo_atencion.html'
    model = GrupoAtencion
    context_object_name = 'grupo_atencion'
    form_class = GrupoAtencionForm
    formset_agente_grupo_atencion = AgentesGrupoAtencionFormSet
    queryset = GrupoAtencion.objects.all()

    def get_context_data(self, **kwargs):
        context = super(
            GrupoAtencionUpdateView, self).get_context_data(**kwargs)

        if 'formset_agente_grupo_atencion' not in context:
            context['formset_agente_grupo_atencion'] = \
            self.formset_agente_grupo_atencion(
                instance=self.object
            )
        return context

    def form_valid(self, form):
        return self.process_all_forms_in_tx(form, update=True)

    def form_invalid(self, form):
        return self.process_all_forms_in_tx(form, update=True)

    def get_success_url(self):
        return reverse('lista_derivacion')


class GrupoAtencionDeleteView(DeleteView):
    """
    Esta vista se encarga de la eliminación del
    objeto GrupAtencion seleccionado.
    """

    model = GrupoAtencion
    template_name = 'derivacion/elimina_grupo_atencion.html'
    queryset = GrupoAtencion.objects.all()

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        success_url = self.get_success_url()

        # Marcamos el grupo de atención como borrado.
        self.object.borrar()

        message = '<strong>Operación Exitosa!</strong>\
        Se llevó a cabo con éxito la eliminación del Grupo de Atención.'

        messages.add_message(
            self.request,
            messages.SUCCESS,
            message,
        )
        return HttpResponseRedirect(success_url)

    def get_success_url(self):
        return reverse('lista_derivacion')


# =============================================================================
# Base Datos Contacto
# =============================================================================


class BaseDatosContactoListView(ListView):
    """
    Esta vista es para generar el listado de
    Lista de Contactos.
    """

    template_name = 'base_datos_contacto/lista_base_datos_contacto.html'
    context_object_name = 'bases_datos_contacto'
    model = BaseDatosContacto

    def get_queryset(self):
        queryset = BaseDatosContacto.objects.obtener_definidas()
        return queryset


class BaseDatosContactoCreateView(CreateView):
    """
    Esta vista crea una instancia de BaseDatosContacto
    sin definir, lo que implica que no esta disponible
    hasta que se procese su definición.
    """

    template_name = 'base_datos_contacto/nueva_edita_base_datos_contacto.html'
    model = BaseDatosContacto
    context_object_name = 'base_datos_contacto'
    form_class = BaseDatosContactoForm

    def form_valid(self, form):
        nombre_archivo_importacion =\
            self.request.FILES['archivo_importacion'].name

        self.object = form.save(commit=False)
        self.object.nombre_archivo_importacion = nombre_archivo_importacion
        self.object.save()
        return redirect(self.get_success_url())

    def get_success_url(self):
        return reverse(
            'define_base_datos_contacto',
            kwargs={"pk": self.object.pk})


class DefineBaseDatosContactoView(UpdateView):
    """
    Esta vista se obtiene un resumen de la estructura
    del archivo a importar y la presenta al usuario para
    que seleccione en que columna se encuentra el teléfono.
    Guarda la posición de la columna como entero y llama a
    importar los teléfono del archivo que se guardo.
    Si la importación resulta bien, llama a definir el objeto
    BaseDatosContacto para que esté disponible.
    """

    template_name = 'base_datos_contacto/define_base_datos_contacto.html'
    model = BaseDatosContacto
    context_object_name = 'base_datos_contacto'

    def get_context_data(self, **kwargs):
        context = super(
            DefineBaseDatosContactoView, self).get_context_data(**kwargs)

        base_datos_contacto = get_object_or_404(
            BaseDatosContacto, pk=self.kwargs['pk']
        )

        parser_archivo = autodetectar_parser(
            base_datos_contacto.nombre_archivo_importacion)

        estructura_archivo = None
        try:
            estructura_archivo = parser_archivo.get_file_structure(
                base_datos_contacto.archivo_importacion.file)
        except FtsParserCsvDelimiterError:
            message = '<strong>Operación Errónea!</strong> \
            No se pudo determinar el delimitador a ser utilizado \
            en el archivo csv. No se pudo llevar a cabo el procesamiento \
            de sus datos.'

            messages.add_message(
                self.request,
                messages.ERROR,
                message,
            )
        except FtsParserMinRowError:
            message = '<strong>Operación Errónea!</strong> \
            El archivo que seleccionó posee menos de 3 filas.\
            No se pudo llevar a cabo el procesamiento de sus datos.'

            messages.add_message(
                self.request,
                messages.ERROR,
                message,
            )
        except FtsParserOpenFileError:
            message = '<strong>Operación Errónea!</strong> \
            El archivo que seleccionó no pudo ser abierto para su \
            para su procesamiento.'

            messages.add_message(
                self.request,
                messages.ERROR,
                message,
            )

        context['estructura_archivo'] = estructura_archivo
        return context

    def form_invalid(self, form):
        return self.render_to_response(self.get_context_data(error=True))

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()

        if 'telefono' in self.request.POST:
            self.object.columna_datos = int(self.request.POST['telefono'])
            self.object.save()

            parser_archivo = autodetectar_parser(
                self.object.nombre_archivo_importacion)

            try:
                self.object.importa_contactos(parser_archivo)
                self.object.define()

                message = '<strong>Operación Exitosa!</strong>\
                Se llevó a cabo con éxito la creación de\
                la Base de Datos de Contactos.'

                messages.add_message(
                    self.request,
                    messages.SUCCESS,
                    message,
                )
                return redirect(self.get_success_url())
            except FtsParserMaxRowError:
                message = '<strong>Operación Errónea!</strong> \
                El archivo que seleccionó posee mas registros de los permitidos\
                para ser importados.'

                messages.add_message(
                    self.request,
                    messages.ERROR,
                    message,
                )
                return redirect(reverse('lista_base_datos_contacto'))
        return super(DefineBaseDatosContactoView, self).post(
            request, *args, **kwargs)

    def get_success_url(self):
        return reverse('lista_base_datos_contacto')


class DepuraBaseDatosContactoView(DeleteView):
    """
    Esta vista se encarga de la depuración del
    objeto Base de Datos seleccionado.
    """

    model = BaseDatosContacto
    template_name = 'base_datos_contacto/depura_base_datos_contacto.html'

    def get_success_url(self):
        return reverse(
            'lista_base_datos_contacto',
        )

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        success_url = self.get_success_url()

        if self.object.verifica_en_uso():
            message = """<strong>¡Cuidado!</strong>
            La Base Datos Contacto que intenta depurar esta siendo utilizada
            por alguna campaña. No se llevará a cabo la depuración la misma 
            mientras esté siendo utilizada."""
            messages.add_message(
                self.request,
                messages.WARNING,
                message,
            )
            return HttpResponseRedirect(success_url)

        try:
            self.object.procesa_depuracion()
        except FtsDepuraBaseDatoContactoError:
            message = """<strong>¡Operación Errónea!</strong>
            La Base Datos Contacto no se pudo depurar."""
            messages.add_message(
                self.request,
                messages.ERROR,
                message,
            )
            return HttpResponseRedirect(success_url)
        else:
            message = '<strong>Operación Exitosa!</strong>\
            Se llevó a cabo con éxito la depuración de la Base de Datos.'

            messages.add_message(
                self.request,
                messages.SUCCESS,
                message,
            )
            return HttpResponseRedirect(success_url)


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

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        success_url = self.get_success_url()

        # Eliminamos la tabla generada en la depuración de la campaña.
        from fts_daemon.models import EventoDeContacto
        EventoDeContacto.objects.eliminar_tabla_eventos_de_contacto_depurada(
            self.object.pk)

        # Marcamos la campaña como borrada.
        self.object.borrar()

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
            kwargs={"pk": self.object.pk})


class CampanaUpdateView(UpdateView):
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
            kwargs={"pk": self.object.pk})


class AudioCampanaCreateView(UpdateView):
    """
    Esta vista actuaiza un objeto Campana
    con el upload del audio.
    """

    template_name = 'campana/audio_campana.html'
    model = Campana
    context_object_name = 'campana'
    form_class = AudioForm

    def form_valid(self, form):
        self.object = form.save()

        try:
            convertir_audio_de_campana(self.object)
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

    def get_success_url(self):
        return reverse(
            'audio_campana',
            kwargs={"pk": self.object.pk})


class CalificacionCampanaCreateView(CreateView):
    """
    Esta vista crea uno o varios objetos Calificación
    para la Campana que se este creando.
    Inicializa el form con campo campana (hidden)
    con el id de campana que viene en la url.
    """

    template_name = 'campana/calificacion_campana.html'
    model = Calificacion
    context_object_name = 'calificacion'
    form_class = CalificacionForm

    def get_initial(self):
        initial = super(CalificacionCampanaCreateView, self).get_initial()
        if 'pk' in self.kwargs:
            initial.update({
                'campana': self.kwargs['pk'],
            })
        return initial

    def get_context_data(self, **kwargs):
        context = super(
            CalificacionCampanaCreateView, self).get_context_data(**kwargs)

        self.campana = get_object_or_404(
            Campana, pk=self.kwargs['pk']
        )
        context['campana'] = self.campana
        return context

    def get_success_url(self):
        return reverse(
            'calificacion_campana',
            kwargs={"pk": self.kwargs['pk']}
        )


class CalificacionCampanaDeleteView(DeleteView):
    """
    Esta vista se encarga de la eliminación del
    objeto Calificación seleccionado.
    """

    model = Calificacion
    template_name = 'campana/elimina_calificacion_campana.html'

    def get_object(self, queryset=None):
        calificacion = super(CalificacionCampanaDeleteView, self).get_object(
            queryset=None)

        self.campana = calificacion.campana
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


class OpcionCampanaCreateView(CreateView):
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

    def get_initial(self):
        initial = super(OpcionCampanaCreateView, self).get_initial()
        if 'pk' in self.kwargs:
            initial.update({
                'campana': self.kwargs['pk'],
            })
        return initial

    def get_context_data(self, **kwargs):
        context = super(
            OpcionCampanaCreateView, self).get_context_data(**kwargs)

        self.campana = get_object_or_404(
            Campana, pk=self.kwargs['pk']
        )
        context['campana'] = self.campana
        return context

    def get_success_url(self):
        return reverse(
            'opcion_campana',
            kwargs={"pk": self.kwargs['pk']}
        )


class OpcionCampanaDeleteView(DeleteView):
    """
    Esta vista se encarga de la eliminación del
    objeto Opciión seleccionado.
    """

    model = Opcion
    template_name = 'campana/elimina_opcion_campana.html'

    def get_object(self, queryset=None):
        opcion = super(OpcionCampanaDeleteView, self).get_object(
            queryset=None)

        self.campana = opcion.campana
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


class ActuacionCampanaCreateView(CreateView):
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

    def get_initial(self):
        initial = super(ActuacionCampanaCreateView, self).get_initial()
        if 'pk' in self.kwargs:
            initial.update({
                'campana': self.kwargs['pk'],
            })
        return initial

    def get_context_data(self, **kwargs):
        context = super(
            ActuacionCampanaCreateView, self).get_context_data(**kwargs)

        self.campana = get_object_or_404(
            Campana, pk=self.kwargs['pk']
        )
        context['campana'] = self.campana
        context['actuaciones_validas'] =\
            self.campana.obtener_actuaciones_validas()
        return context

    def form_valid(self, form):
        form_valid = super(ActuacionCampanaCreateView, self).form_valid(form)

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
            'actuacion_campana',
            kwargs={"pk": self.kwargs['pk']}
        )


class ActuacionCampanaDeleteView(DeleteView):
    """
    Esta vista se encarga de la eliminación del
    objeto Actuación seleccionado.
    """

    model = Actuacion
    template_name = 'campana/elimina_actuacion_campana.html'

    def get_object(self, queryset=None):
        actuacion = super(ActuacionCampanaDeleteView, self).get_object(
            queryset=None)

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
            'actuacion_campana',
            kwargs={"pk": self.campana.pk}
        )


class ConfirmaCampanaMixin(UpdateView):

    """
    Esta vista confirma la creación de un objeto
    Campana. Imprime el resumen del objeto y si
    es aceptado, cambia el estado del objeto a ACTIVA.
    Si el objeto ya esta ACTIVA, redirecciona
    al listado.
    """

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

            # END: with transaction.atomic()

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
            #TODO: Implementar la cancelación.

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
                reverse(
                    'audio_campana',
                    kwargs={"pk": campana.pk}))
        return super(ConfirmaCampanaView, self).get(request, *args, **kwargs)


class FinalizaCampanaView(RedirectView):
    """
    Esta vista actualiza la campañana finalizándola.
    """

    pattern_name = 'lista_campana'

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


class TipoRecicladoCampanaView(FormView):
    """
    Esta vista presenta la elección del tipo de reciclado iniciando el
    proceso de reciclado de una camapan.
    """

    template_name = 'campana/reciclado/campana_tipo_reciclado.html'
    form_class = TipoRecicladoForm

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
                CampanaTipoRecicladoInvalidoError) as error:
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


class DetalleCampanView(DetailView):
    """
    Muestra el detalle de la campaña.
    """
    template_name = 'campana/detalle_campana.html'
    context_object_name = 'campana'
    model = Campana


class ExportaReporteCampanaView(UpdateView):
    """
    Esta vista invoca a generar un csv de reporte de la campana.
    """

    model = Campana
    context_object_name = 'campana'

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()

        url = self.object.obtener_url_reporte_csv_descargar()

        return redirect(url)


# =============================================================================
# Templates
# =============================================================================


class TemplateMixin(object):

    def get_context_data(self, **kwargs):
        context = super(TemplateMixin, self).get_context_data(**kwargs)
        context['es_template'] = True
        return context


class TemplateListView(TemplateMixin, ListView):
    """
    Esta vista lista los objetos Capanas-->Templates activos.
    """

    template_name = 'template/lista_template.html'
    context_object_name = 'campanas'
    model = Campana

    def get_context_data(self, **kwargs):
        context = super(TemplateListView, self).get_context_data(**kwargs)
        context['templates_activos'] = \
            Campana.objects_template.obtener_activos()
        return context


class TemplateDeleteView(TemplateMixin, DeleteView):
    """
    Esta vista se encarga de la eliminación del
    objeto Campana-->Template.
    """

    model = Campana
    template_name = 'campana/elimina_campana.html'

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        success_url = self.get_success_url()

        self.object.borrar_template()

        message = '<strong>Operación Exitosa!</strong>\
        Se llevó a cabo con éxito la eliminación del Template.'

        messages.add_message(
            self.request,
            messages.SUCCESS,
            message,
        )
        return HttpResponseRedirect(success_url)

    def get_success_url(self):
        return reverse('lista_template')


class TemplateCreateView(TemplateMixin, CreateView):
    """
    Esta vista crea un objeto Campana-->Template.
    Por defecto su estado es EN_DEFICNICION,
    Redirecciona a crear las opciones para esta
    Campana.
    """
    template_name = 'campana/nueva_edita_campana.html'
    model = Campana
    context_object_name = 'campana'
    form_class = TemplateForm

    def form_valid(self, form):
        self.object = form.save()

        self.object.es_template = True
        self.object.estado = Campana.ESTADO_TEMPLATE_EN_DEFINICION
        self.object.save()
        return redirect(self.get_success_url())

    def get_success_url(self):
        return reverse(
            'audio_template',
            kwargs={"pk": self.object.pk})


class TemplateaUpdateView(TemplateMixin, UpdateView):
    """
    Esta vista actualiza un objeto Campana-->Template.
    """

    template_name = 'campana/nueva_edita_campana.html'
    model = Campana
    context_object_name = 'campana'
    form_class = TemplateForm

    def get_success_url(self):
        return reverse(
            'audio_template',
            kwargs={"pk": self.object.pk})


class DetalleTemplateView(TemplateMixin, DetalleCampanView):
    pass


class AudioTemplateCreateView(TemplateMixin, AudioCampanaCreateView):

    def get_success_url(self):
        return reverse(
            'audio_template',
            kwargs={"pk": self.object.pk})


class CalificacionTemplateCreateView(TemplateMixin,
                                     CalificacionCampanaCreateView):
    def get_success_url(self):
        return reverse(
            'calificacion_template',
            kwargs={"pk": self.kwargs['pk']}
        )


class CalificacionTemplateDeleteView(TemplateMixin,
                                     CalificacionCampanaDeleteView):
    def get_success_url(self):
        return reverse(
            'calificacion_template',
            kwargs={"pk": self.campana.pk}
        )


class OpcionTemplateCreateView(TemplateMixin, OpcionCampanaCreateView):
    def get_success_url(self):
        return reverse(
            'opcion_template',
            kwargs={"pk": self.kwargs['pk']}
        )


class OpcionTemplateDeleteView(TemplateMixin, OpcionCampanaDeleteView):
    def get_success_url(self):
        return reverse(
            'opcion_template',
            kwargs={"pk": self.campana.pk}
        )


class ActuacionTemplateCreateView(TemplateMixin, ActuacionCampanaCreateView):
    def get_success_url(self):
        return reverse(
            'actuacion_template',
            kwargs={"pk": self.kwargs['pk']}
        )

    def form_valid(self, form):
        self.object = form.save()
        return redirect(self.get_success_url())


class ActuacionTemplateDeleteView(TemplateMixin, ActuacionCampanaDeleteView):
    def get_success_url(self):
        return reverse(
            'actuacion_template',
            kwargs={"pk": self.campana.pk}
        )

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        success_url = self.get_success_url()
        self.object.delete()

        message = '<strong>Operación Exitosa!</strong>\
        Se llevó a cabo con éxito la eliminación de la Actuación.'

        messages.add_message(
            self.request,
            messages.SUCCESS,
            message,
        )

        return HttpResponseRedirect(success_url)


class ConfirmaTemplateView(TemplateMixin, UpdateView):
    template_name = 'campana/confirma_campana.html'
    model = Campana
    context_object_name = 'campana'
    form_class = ConfirmaForm

    def form_valid(self, form):
        if 'confirma' in self.request.POST:
            campana = self.object

            if not campana.valida_grupo_atencion():
                message = '<strong>Operación Errónea!</strong> \
                    EL Grupo Atención seleccionado en el proceso de creación \
                    del template ha sido eliminado. Debe seleccionar uno \
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
                    creación del template ha sido eliminada. Debe \
                    seleccionar uno válido.'
                messages.add_message(
                    self.request,
                    messages.ERROR,
                    message,
                )
                return self.form_invalid(form)

            campana.activar_template()

            message = '<strong>Operación Exitosa!</strong> \
                Se llevó a cabo con éxito la creación del Template.'
            messages.add_message(
                self.request,
                messages.SUCCESS,
                message,
            )

            return redirect(self.get_success_url())

        elif 'cancela' in self.request.POST:
            pass
            #TODO: Implementar la cancelación.

    def get_success_url(self):
        return reverse('lista_template')


class CreaCampanaTemplateView(TemplateMixin, RedirectView):
    permanent = False
    url = None

    def get(self, request, *args, **kwargs):
        template = get_object_or_404(
            Campana, pk=self.kwargs['pk']
        )
        campana = Campana.objects_template.crea_campana_de_template(template)

        self.url = reverse('datos_basicos_campana', kwargs={"pk": campana.pk})

        return super(CreaCampanaTemplateView, self).get(request, *args,
                                                        **kwargs)


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
        context['campanas_ejecucion'] = Campana.objects.obtener_ejecucion()
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


# =============================================================================
# Daemon
# =============================================================================

statistics_service = StatisticsService(cache=get_cache('default'))


def _update_context_with_statistics(context):
    """Metodo utilitario. Recibe un contexto, y setea en el
    las estadisticas del Daemon."""
    daemon_stats = statistics_service.get_statistics()
    stats_timestamp = daemon_stats.get('_time', None)
    if stats_timestamp is None:
        context['daemon_stats_valid'] = False
    else:
        delta = timezone.now() - stats_timestamp
        if delta.days != 0:
            context['daemon_stats_valid'] = False
            logger.warn("_update_context_with_statistics(): delta.days: %s",
                        delta.days)
        # elif delta.seconds == 0 and delta.microseconds > 20000:
        elif delta.seconds > settings.FTS_DAEMON_STATS_VALIDEZ:
            context['daemon_stats_valid'] = False
        else:
            context['daemon_stats_valid'] = True

    context['daemon_stats'] = daemon_stats


class DaemonStatusView(TemplateView):
    """Devuelve HTML con informacion de status / estadisticas
    del Daemon"""

    template_name = "estado/daemon_status.html"

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super(DaemonStatusView, self).dispatch(*args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(DaemonStatusView, self).get_context_data(**kwargs)
        _update_context_with_statistics(context)
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
            convertir_audio_de_archivo_de_audio_globales(self.object)
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

    def form_valid(self, form):
        self.object = form.save()

        if self.request.FILES.get('audio_original'):
            try:
                convertir_audio_de_archivo_de_audio_globales(self.object)
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
