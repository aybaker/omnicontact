# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib import messages
from django.core.urlresolvers import reverse
from django.http.response import HttpResponse
from django.shortcuts import redirect, get_object_or_404
from django.views.generic import (
    CreateView, ListView,
    UpdateView, DetailView)

from fts_web.forms import (
    ActuacionForm, AgentesGrupoAtencionFormSet, CampanaForm,
    CalificacionForm, ConfirmaForm, GrupoAtencionForm,
    BaseDatosContactoForm, OpcionForm)
from fts_web.models import (
    Actuacion, Calificacion, Campana, GrupoAtencion,
    BaseDatosContacto, IntentoDeContacto, Opcion)
from fts_web.parser import autodetectar_parser


#===============================================================================
# Grupos de Atención
#===============================================================================


class GrupoAtencionListView(ListView):
    """
    Esta vista es para generar el listado de
    GrupoAtencion.
    """

    template_name = 'grupo_atencion/lista_grupo_atencion.html'
    context_object_name = 'grupos_atencion'
    model = GrupoAtencion

    #def get_queryset(self):
    #    queryset = GrupoAtencion.objects.filtrar_activos()
    #    return queryset


class GrupoAtencionMixin(object):
    """
    Este mixin procesa y valida
    los formularios en la creación y edición
    de objetos GrupoAtencion.
    """

    def process_all_forms(self, form):
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

            return redirect(self.get_success_url())
        else:
            if form.is_valid():
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

    template_name = 'grupo_atencion/grupo_atencion.html'
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
        return self.process_all_forms(form)

    def form_invalid(self, form):
        return self.process_all_forms(form)

    def get_success_url(self):
        message = '<strong>Operación Exitosa!</strong>\
        Se llevó a cabo con éxito la creación del\
        Grupo de Atención.'

        messages.add_message(
            self.request,
            messages.SUCCESS,
            message,
        )

        return reverse('lista_grupo_atencion')


# class GrupoAtencionUpdateView(UpdateView, GrupoAtencionMixin):
#     """
#     Esta vista actualiza el objeto GrupoAtencion
#     seleccionado.
#     """

#     template_name = 'grupo_atencion/grupo_atencion.html'
#     model = GrupoAtencion
#     context_object_name = 'grupo_atencion'
#     form_class = GrupoAtencionForm
#     formset_agente_grupo_atencion = AgentesGrupoAtencionFormSet

#     def get_context_data(self, **kwargs):
#         context = super(
#             GrupoAtencionUpdateView, self).get_context_data(**kwargs)

#         if 'formset_agente_grupo_atencion' not in context:
#             context['formset_agente_grupo_atencion'] = \
#             self.formset_agente_grupo_atencion(
#                 instance=self.object
#             )
#         return context

#     def form_valid(self, form):
#         return self.process_all_forms(form)

#     def form_invalid(self, form):
#         return self.process_all_forms(form)

#     def get_success_url(self):
#         message = '<strong>Operación Exitosa!</strong>\
#         Se llevó a cabo con éxito la actualización del\
#         Grupo de Atención.'

#         messages.add_message(
#             self.request,
#             messages.SUCCESS,
#             message,
#         )

#         return reverse(
#             'edita_grupo_atencion',
#             kwargs={"pk": self.object.pk})


# class GrupoAtencionDeleteView(DeleteView):
#     """
#     Esta vista se encarga de la eliminación del
#     objeto GrupAtencion seleccionado.
#     """

#     model = GrupoAtencion
#     template_name = 'grupo_atencion/elimina_grupo_atencion.html'

#     def get_success_url(self):
#         message = '<strong>Operación Exitosa!</strong>\
#         Se llevó a cabo con éxito la eliminación del\
#         Grupo de Atención.'

#         messages.add_message(
#             self.request,
#             messages.SUCCESS,
#             message,
#         )

#         return reverse('lista_grupo_atencion')


#===============================================================================
# Base Datos Contacto
#===============================================================================


class BaseDatosContactoListView(ListView):
    """
    Esta vista es para generar el listado de
    Lista de Contactos.
    """

    template_name = 'base_datos_contacto/lista_base_datos_contacto.html'
    context_object_name = 'bases_datos_contacto'
    model = BaseDatosContacto


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
        estructura_archivo = parser_archivo.get_file_structure(
            base_datos_contacto.archivo_importacion.file)

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

            importacion = self.object.importa_contactos(parser_archivo)
            if importacion:
                self.object.define()

                return redirect(self.get_success_url())
        return super(DefineBaseDatosContactoView, self).post(
            request, *args, **kwargs)

    def get_success_url(self):
        message = '<strong>Operación Exitosa!</strong>\
        Se llevó a cabo con éxito la creación de\
        la Base de Datos de Contactos.'

        messages.add_message(
            self.request,
            messages.SUCCESS,
            message,
        )

        return reverse('lista_base_datos_contacto')


# class BaseDatosContactoUpdateView(UpdateView, BaseDatosContactoMixin):
#     """
#     Esta vista actualiza el objeto
#     BaseDatosContacto seleccionado.
#     """

#     template_name = 'base_datos_contacto/nueva_edita_listas_contacto.html'
#     model = BaseDatosContacto
#     context_object_name = 'base_datos_contacto'
#     form_class = BaseDatosContactoForm
#     form_file = FileForm

#     def get_context_data(self, **kwargs):
#         context = super(
#             BaseDatosContactoUpdateView, self).get_context_data(**kwargs)

#         if 'form_file' not in context:
#             context['form_file'] = self.form_file()
#         return context

#     def form_valid(self, form):
#         return self.process_all_forms(form)

#     def form_invalid(self, form):
#         return self.process_all_forms(form)

#     def get_success_url(self):
#         message = '<strong>Operación Exitosa!</strong>\
#         Se llevó a cabo con éxito la actualización de\
#         la Base de Datos de Contactos.'

#         messages.add_message(
#             self.request,
#             messages.SUCCESS,
#             message,
#         )

#         return reverse(
#             'edita_base_datos_contacto',
#             kwargs={"pk": self.object.pk})


#===============================================================================
# Campaña
#===============================================================================


class CampanaListView(ListView):
    """
    Esta vista realiza el listado de
    los objetos Campanas que esten activas.
    """

    template_name = 'campana/lista_campana.html'
    context_object_name = 'campanas'
    model = Campana

    def get_queryset(self):
        queryset = Campana.objects.obtener_activas()
        return queryset


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
            'calificacion_campana',
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
        return context

    def get_success_url(self):
        return reverse(
            'actuacion_campana',
            kwargs={"pk": self.kwargs['pk']}
        )


class ConfirmaCampanaView(UpdateView):
    """
    Esta vista confirma la creación de un objeto
    Campana. Imprime el resumen del objeto y si
    es aceptado, cambia el estado del objeto a ACTIVA.
    Si el objeto ya esta ACTIVA, redirecciona
    al listado.
    """

    template_name = 'campana/confirma_campana.html'
    model = Campana
    context_object_name = 'campana'
    form_class = ConfirmaForm

    def get(self, request, *args, **kwargs):
        campana = self.get_object()
        if not campana.estado == Campana.ESTADO_EN_DEFINICION:
            return redirect('lista_campana')
        return super(ConfirmaCampanaView, self).get(request, *args, **kwargs)

    def form_valid(self, form):
        if 'confirma' in self.request.POST:
            campana = self.object
            campana.activar()

            return redirect(self.get_success_url())
        elif 'cancela' in self.request.POST:
            pass
            #TODO: Implementar la cancelación.

    def get_success_url(self):
        message = '<strong>Operación Exitosa!</strong>\
        Se llevó a cabo con éxito la creación de\
        la Campaña.'

        messages.add_message(
            self.request,
            messages.SUCCESS,
            message,
        )

        return reverse('lista_campana')


class PausaCampanaView(UpdateView):
    """
    Esta vista actualiza la campañana pausándola.
    """

    model = Campana
    context_object_name = 'campana'

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()

        self.object.pausar()

        return redirect(self.get_success_url())

    def get_success_url(self):
        message = '<strong>Operación Exitosa!</strong>\
        Se llevó a cabo con éxito el pausado de\
        la Campaña.'

        messages.add_message(
            self.request,
            messages.SUCCESS,
            message,
        )

        return reverse('lista_campana_por_estados')


class ActivaCampanaView(UpdateView):
    """
    Esta vista actualiza la campañana activándola.
    """

    model = Campana
    context_object_name = 'campana'

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()

        self.object.despausar()

        return redirect(self.get_success_url())

    def get_success_url(self):
        message = '<strong>Operación Exitosa!</strong>\
        Se llevó a cabo con éxito la activación de\
        la Campaña.'

        messages.add_message(
            self.request,
            messages.SUCCESS,
            message,
        )

        return reverse('lista_campana_por_estados')


# class CampanaUpdateView(UpdateView):
#     """
#     Esta vista actualiza un objeto Campana.
#     """

#     template_name = 'campana/nueva_edita_campana.html'
#     model = Campana
#     context_object_name = 'campana'
#     form_class = CampanaForm

#     def get_success_url(self):
#         message = '<strong>Operación Exitosa!</strong>\
#         Se llevó a cabo con éxito la actualización de\
#         la Campaña.'

#         messages.add_message(
#             self.request,
#             messages.SUCCESS,
#             message,
#         )

#         return reverse(
#             'edita_campana',
#             kwargs={"pk": self.object.pk})


#===============================================================================
# Estados
#===============================================================================


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

    #def get_queryset(self):
        # FIXME: para setear variables, sobreescribir get_context_data()
        # ya que según la API, get_queryset() es para otras cosas.
        # (ya está implementado más abajo)
        # query_dict = {
        #     'activas': Campana.objects.obtener_activas(),
        #     'finalizadas': Campana.objects.obtener_finalizadas(),
        # }
        # return query_dict

    def get_context_data(self, **kwargs):
        context = super(CampanaPorEstadoListView, self).get_context_data(
           **kwargs)
        context['activas'] = Campana.objects.obtener_activas()
        context['pausadas'] = Campana.objects.obtener_pausadas()
        context['finalizadas'] = Campana.objects.obtener_finalizadas()
        return context


class CampanaPorEstadoDetailView(DetailView):
    """Muestra el estado de la campaña con la lista de
    contactos asociados, y el estado de c/u de dichos contactos
    """
    template_name = 'estado/detalle_estado_campana.html'
    model = Campana


#===============================================================================
# AGI
#===============================================================================

def registar_llamada_contestada(request, call_id):
    # TODO: chequear host origen
    intento = IntentoDeContacto.objects.get(pk=call_id)
    intento.registra_contesto()
    return HttpResponse('ok')
