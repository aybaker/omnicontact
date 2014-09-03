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

from fts_web.views_campana import *
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
# Derivación
# =============================================================================


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

        creacion_base_datos = CreacionBaseDatosService()
        creacion_base_datos.genera_base_dato_contacto(self.object)

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

    # @@@@@@@@@@@@@@@@@@@@

    def obtiene_estructura_archivo(self, pk):
        base_datos_contacto = get_object_or_404(
            BaseDatosContacto, pk=pk
        )

        parser = ParserCsv()
        estructura_archivo = None
        try:
            estructura_archivo = parser.get_file_structure(
                base_datos_contacto.archivo_importacion.file)
            return estructura_archivo

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

    def get_context_data(self, **kwargs):
        context = super(
            DefineBaseDatosContactoView, self).get_context_data(**kwargs)

        estructura_archivo = self.obtiene_estructura_archivo(self.kwargs['pk'])
        context['estructura_archivo'] = estructura_archivo
        context['datos_extras'] = BaseDatosContacto.DATOS_EXTRAS
        return context

    def form_invalid(self, form):
        return self.render_to_response(self.get_context_data(error=True))

    def post(self, request, *args, **kwargs):

        self.object = self.get_object()

        dic_metadata = {}
        if 'telefono' in self.request.POST:

            columan_con_telefono = int(self.request.POST['telefono'])
            dic_metadata['columna_con_telefono'] = columan_con_telefono

            estructura_archivo = self.obtiene_estructura_archivo(
                self.kwargs['pk'])
            lista_columnas_fechas = []
            lista_columnas_horas = []
            for columna in estructura_archivo.keys():
                dato_extra = self.request.POST.get(
                    'datos-extras-{0}'.format(columna), None)
                if dato_extra == BaseDatosContacto.DATO_EXTRA_FECHA:
                    lista_columnas_fechas.append(columna)
                elif dato_extra == BaseDatosContacto.DATO_EXTRA_HORA:
                    lista_columnas_horas.append(columna)

            dic_metadata['columnas_con_fecha'] = lista_columnas_fechas
            dic_metadata['columnas_con_hora'] = lista_columnas_horas

            creacion_base_datos = CreacionBaseDatosService()
            creacion_base_datos.guarda_metadata(self.object, dic_metadata)

            try:
                creacion_base_datos.importa_contactos(self.object)
            except FtsParserMaxRowError:
                message = '<strong>Operación Errónea!</strong> \
                          El archivo que seleccionó posee mas registros de los\
                          permitidos para ser importados.'

                messages.add_message(
                    self.request,
                    messages.ERROR,
                    message,
                )
                return redirect(reverse('lista_base_datos_contacto'))
            else:
                creacion_base_datos.define_base_dato_contacto(self.object)

                message = '<strong>Operación Exitosa!</strong>\
                          Se llevó a cabo con éxito la creación de\
                          la Base de Datos de Contactos.'

                messages.add_message(
                    self.request,
                    messages.SUCCESS,
                    message,
                )
                return redirect(self.get_success_url())

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
