# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from django.contrib import messages
from django.core.urlresolvers import reverse
from django.http.response import HttpResponseRedirect
from django.shortcuts import redirect, get_object_or_404
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.views.generic.list import ListView
from fts_web.errors import FtsParserCsvDelimiterError, FtsParserMinRowError, \
    FtsParserOpenFileError, FtsParserMaxRowError, \
    FtsDepuraBaseDatoContactoError
from fts_web.forms import (BaseDatosContactoForm, DefineNombreColumnaForm,
                           DefineColumnaTelefonoForm, DefineDatosExtrasForm,
                           PrimerLineaEncabezadoForm)
from fts_web.models import BaseDatosContacto
from fts_web.parser import ParserCsv
from fts_web.services.base_de_datos_contactos import (CreacionBaseDatosService,
                                                      PredictorMetadataService)
import logging as logging_


logger = logging_.getLogger(__name__)

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
        nombre_archivo_importacion = \
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

    def dispatch(self, request, *args, **kwargs):
        self.base_datos_contacto = \
            BaseDatosContacto.objects.obtener_en_definicion_para_editar(
                self.kwargs['pk'])
        return super(DefineBaseDatosContactoView, self).dispatch(request,
                                                                 *args,
                                                                 **kwargs)

    def obtiene_previsualizacion_archivo(self):

        parser = ParserCsv()
        estructura_archivo = None
        try:

            base_datos_contacto = get_object_or_404(
                BaseDatosContacto, pk=self.base_datos_contacto.pk
            )
            # FIXME: Modificar el pasar por parámetro el archivo abierto.
            return parser.previsualiza_archivo(
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

    def get_context_data(self, **kwargs):
        context = super(
            DefineBaseDatosContactoView, self).get_context_data(**kwargs)

        estructura_archivo = self.obtiene_previsualizacion_archivo()
        context['estructura_archivo'] = estructura_archivo

        predictor_metadata = PredictorMetadataService()
        metadata = predictor_metadata.inferir_metadata_desde_lineas(
            estructura_archivo)

        initial_predecido_columna_telefono = \
            {'telefono': metadata.columna_con_telefono}

        initial_predecido_datos_extras = dict(
            [('datos-extras-{0}'.format(col),
                BaseDatosContacto.DATO_EXTRA_FECHA)
                for col in metadata.columnas_con_fecha])

        initial_predecido_datos_extras.update(dict(
            [('datos-extras-{0}'.format(col),
                BaseDatosContacto.DATO_EXTRA_HORA)
                for col in metadata.columnas_con_hora]))

        initial_predecido_nombre_columnas = dict(
            [('nombre-columna-{0}'.format(i), nombre)
                for i, nombre in enumerate(metadata.nombres_de_columnas)])

        initial_predecido_encabezado = {'es_encabezado':
                                        metadata.primer_fila_es_encabezado}

        if 'form_columna_telefono' not in context:
            form_columna_telefono = DefineColumnaTelefonoForm(
                cantidad_columnas=metadata.cantidad_de_columnas,
                initial=initial_predecido_columna_telefono)
            context['form_columna_telefono'] = form_columna_telefono

        if 'form_datos_extras' not in context:
            form_datos_extras = DefineDatosExtrasForm(
                cantidad_columnas=metadata.cantidad_de_columnas,
                initial=initial_predecido_datos_extras)
            context['form_datos_extras'] = form_datos_extras

        if 'form_nombre_columnas' not in context:
            form_nombre_columnas = DefineNombreColumnaForm(
                cantidad_columnas=metadata.cantidad_de_columnas,
                initial=initial_predecido_nombre_columnas)
            context['form_nombre_columnas'] = form_nombre_columnas

        if 'form_primer_linea_encabezado' not in context:
            form_primer_linea_encabezado = PrimerLineaEncabezadoForm(
                initial=initial_predecido_encabezado)
            context['form_primer_linea_encabezado'] =\
                form_primer_linea_encabezado

        return context

    def form_invalid(self, form_columna_telefono, form_datos_extras,
                     form_nombre_columnas, form_primer_linea_encabezado):

        message = '<strong>Operación Errónea!</strong> \
                  Verifique los datos seleccionados.'

        messages.add_message(
            self.request,
            messages.ERROR,
            message,
        )

        return self.render_to_response(self.get_context_data(
            form_columna_telefono=form_columna_telefono,
            form_datos_extras=form_datos_extras,
            form_nombre_columnas=form_nombre_columnas,
            form_primer_linea_encabezado=form_primer_linea_encabezado))

    def post(self, request, *args, **kwargs):

        self.object = self.get_object()

        estructura_archivo = self.obtiene_previsualizacion_archivo()
        cantidad_columnas = len(estructura_archivo[0])

        form_columna_telefono = DefineColumnaTelefonoForm(
            cantidad_columnas, request.POST)
        form_datos_extras = DefineDatosExtrasForm(
            cantidad_columnas, request.POST)
        form_nombre_columnas = DefineNombreColumnaForm(
            cantidad_columnas, request.POST)
        form_primer_linea_encabezado = PrimerLineaEncabezadoForm(request.POST)

        if (form_columna_telefono.is_valid() and
                form_nombre_columnas.is_valid()):

            columna_con_telefono = int(self.request.POST['telefono'])

            lista_columnas_fechas = []
            lista_columnas_horas = []
            lista_nombre_columnas = []
            for columna, _ in enumerate(estructura_archivo[0]):
                dato_extra = self.request.POST.get(
                    'datos-extras-{0}'.format(columna), None)
                if dato_extra == BaseDatosContacto.DATO_EXTRA_FECHA:
                    lista_columnas_fechas.append(columna)
                elif dato_extra == BaseDatosContacto.DATO_EXTRA_HORA:
                    lista_columnas_horas.append(columna)

                lista_nombre_columnas.append(self.request.POST.get(
                    'nombre-columna-{0}'.format(columna), None))

            metadata = self.object.get_metadata()
            metadata.cantidad_de_columnas = cantidad_columnas
            metadata.columna_con_telefono = columna_con_telefono
            metadata.columnas_con_fecha = lista_columnas_fechas
            metadata.columnas_con_hora = lista_columnas_horas
            metadata.nombres_de_columnas = lista_nombre_columnas

            es_encabezado = False
            if self.request.POST.get('es_encabezado', False):
                es_encabezado = True
            metadata.primer_fila_es_encabezado = es_encabezado

            creacion_base_datos = CreacionBaseDatosService()
            creacion_base_datos.guarda_metadata(self.object)

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

        return self.form_invalid(form_columna_telefono, form_datos_extras,
                                 form_nombre_columnas,
                                 form_primer_linea_encabezado)

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
