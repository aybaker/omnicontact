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
from fts_web.forms import BaseDatosContactoForm
from fts_web.models import BaseDatosContacto
from fts_web.parser import ParserCsv
from fts_web.services.base_de_datos_contactos import CreacionBaseDatosService
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

    def obtiene_estructura_archivo(self, pk):
        # base_datos_contacto = get_object_or_404(
        #     BaseDatosContacto, pk=pk
        # )

        parser = ParserCsv()
        estructura_archivo = None
        try:
            estructura_archivo = parser.get_file_structure(
                self.base_datos_contacto.archivo_importacion.file)
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
