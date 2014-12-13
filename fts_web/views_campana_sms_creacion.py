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

from fts_web.forms import (CampanaForm, CampanaSmsForm,
    ActuacionForm) 
from fts_web.models import (Campana, CampanaSms, OpcionSms,
    Actuacion)

from fts_web.services.creacion_campana import (
    ActivacionCampanaTemplateService, ValidarCampanaError,
    RestablecerDialplanError)

import logging as logging_


logger = logging_.getLogger(__name__)


class CampanaSmsCreateView(CreateView):
    """
    Esta vista crea un objeto CampanaSms.
    """

    template_name = 'campana_sms/nueva_edita_campana_sms.html'
    model = CampanaSms
    context_object_name = 'campana_sms'
    form_class = CampanaSmsForm

    def form_valid(self, form):
        self.object = form.save(commit=False)

        # TODO: Cambiar la creación del identificador y pasarla a un servicio.
        try:
            identificador = \
                CampanaSms.objects.latest('id').identificador_campana_sms + 1
        except CampanaSms.DoesNotExist:
            identificador = 1000

        self.object.identificador_campana_sms = identificador
        self.object.save()

        return super(CampanaSmsCreateView, self).form_valid(form)

    def get_success_url(self):
        return reverse('datos_basicos_campana_sms',
                       kwargs={"pk_campana_sms": self.object.pk})


class CampanaSmsUpdateView(UpdateView):
    """
    Esta vista actualiza un objeto CampanaSms.
    """

    template_name = 'campana_sms/nueva_edita_campana_sms.html'
    model = CampanaSms
    context_object_name = 'campana_sms'
    pk_url_kwarg = 'pk_campana_sms'
    form_class = CampanaSmsForm

    def get_success_url(self):
        return reverse(
            'datos_basicos_campana_sms',
            kwargs={"pk_campana_sms": self.object.pk})

# 
# class CalificacionCampanaCreateView(CheckEstadoCampanaMixin, CreateView):
#     """
#     Esta vista crea uno o varios objetos Calificación
#     para la Campana que se este creando.
#     Inicializa el form con campo campana (hidden)
#     con el id de campana que viene en la url.
#     """
# 
#     # @@@@@@@@@@@@@@@@@@@@
# 
#     template_name = 'campana/calificacion_campana.html'
#     model = Calificacion
#     context_object_name = 'calificacion'
#     form_class = CalificacionForm
# 
#     def get_initial(self):
#         initial = super(CalificacionCampanaCreateView, self).get_initial()
#         initial.update({'campana': self.campana.id})
#         return initial
# 
#     def get_context_data(self, **kwargs):
#         context = super(CalificacionCampanaCreateView,
#                         self).get_context_data(**kwargs)
#         context['campana'] = self.campana
# 
#         return context
# 
#     def get_success_url(self):
#         return reverse(
#             'calificacion_campana',
#             kwargs={"pk_campana": self.kwargs['pk_campana']}
#         )
# 
# 
# class CalificacionCampanaDeleteView(CheckEstadoCampanaMixin, DeleteView):
#     """
#     Esta vista se encarga de la eliminación del
#     objeto Calificación seleccionado.
#     """
# 
#     model = Calificacion
#     template_name = 'campana/elimina_calificacion_campana.html'
# 
#     # @@@@@@@@@@@@@@@@@@@@
# 
#     def get_object(self, queryset=None):
#         # FIXME: Esté método no hace nada, se podría remover.
#         calificacion = super(CalificacionCampanaDeleteView, self).get_object(
#             queryset=None)
#         return calificacion
# 
#     def delete(self, request, *args, **kwargs):
#         message = '<strong>Operación Exitosa!</strong>\
#             Se llevó a cabo con éxito la eliminación de la Calificación.'
# 
#         messages.add_message(
#             self.request,
#             messages.SUCCESS,
#             message,
#         )
#         return super(CalificacionCampanaDeleteView, self).delete(request,
#                                                                  *args,
#                                                                  **kwargs)
# 
#     def get_success_url(self):
#         return reverse('calificacion_campana',
#                        kwargs={"pk_campana": self.campana.pk})
# 
# 
# class OpcionCampanaCreateView(CheckEstadoCampanaMixin, CreateView):
#     """
#     Esta vista crea uno o varios objetos Opcion
#     para la Campana que se este creando.
#     Inicializa el form con campo campana (hidden)
#     con el id de campana que viene en la url.
#     """
# 
#     template_name = 'campana/opciones_campana.html'
#     model = Opcion
#     context_object_name = 'opcion'
#     form_class = OpcionForm
# 
#     # @@@@@@@@@@@@@@@@@@@@
# 
#     def get_initial(self):
#         initial = super(OpcionCampanaCreateView, self).get_initial()
#         initial.update({'campana': self.campana.id})
#         return initial
# 
#     def get_context_data(self, **kwargs):
#         context = super(
#             OpcionCampanaCreateView, self).get_context_data(**kwargs)
#         context['campana'] = self.campana
#         return context
# 
#     def get_success_url(self):
#         return reverse(
#             'opcion_campana',
#             kwargs={"pk_campana": self.kwargs['pk_campana']}
#         )
# 
# 
# class OpcionCampanaDeleteView(CheckEstadoCampanaMixin, DeleteView):
#     """
#     Esta vista se encarga de la eliminación del
#     objeto Opciión seleccionado.
#     """
# 
#     model = Opcion
#     template_name = 'campana/elimina_opcion_campana.html'
# 
#     # @@@@@@@@@@@@@@@@@@@@
# 
#     def get_object(self, queryset=None):
#         # FIXME: Esté método no hace nada, se podría remover.
#         opcion = super(OpcionCampanaDeleteView, self).get_object(
#             queryset=None)
#         return opcion
# 
#     def delete(self, request, *args, **kwargs):
#         message = '<strong>Operación Exitosa!</strong>\
#             Se llevó a cabo con éxito la eliminación de la Opción.'
# 
#         messages.add_message(
#             self.request,
#             messages.SUCCESS,
#             message,
#         )
#         return super(OpcionCampanaDeleteView, self).delete(request,
#                                                            *args, **kwargs)
# 
#     def get_success_url(self):
#         return reverse(
#             'opcion_campana',
#             kwargs={"pk_campana": self.campana.pk}
#         )
# 
# 
# class ActuacionCampanaCreateView(CheckEstadoCampanaMixin, CreateView):
#     """
#     Esta vista crea uno o varios objetos Actuacion
#     para la Campana que se este creando.
#     Inicializa el form con campo campana (hidden)
#     con el id de campana que viene en la url.
#     """
# 
#     template_name = 'campana/actuacion_campana.html'
#     model = Actuacion
#     context_object_name = 'actuacion'
#     form_class = ActuacionForm
# 
#     # @@@@@@@@@@@@@@@@@@@@
# 
#     def get_initial(self):
#         initial = super(ActuacionCampanaCreateView, self).get_initial()
#         initial.update({'campana': self.campana.id})
#         return initial
# 
#     def get_context_data(self, **kwargs):
#         context = super(
#             ActuacionCampanaCreateView, self).get_context_data(**kwargs)
#         context['campana'] = self.campana
#         context['actuaciones_validas'] = \
#             self.campana.obtener_actuaciones_validas()
#         return context
# 
#     def form_valid(self, form):
#         form_valid = super(ActuacionCampanaCreateView, self).form_valid(form)
# 
#         if not self.campana.valida_actuaciones():
#             message = """<strong>¡Cuidado!</strong>
#             Los días del rango de fechas seteados en la campaña NO coinciden
#             con ningún día de las actuaciones programadas. Por consiguiente
#             la campaña NO se ejecutará."""
#             messages.add_message(
#                 self.request,
#                 messages.WARNING,
#                 message,
#             )
# 
#         return form_valid
# 
#     def get_success_url(self):
#         return reverse(
#             'actuacion_campana',
#             kwargs={"pk_campana": self.kwargs['pk_campana']}
#         )
# 
# 
# class ActuacionCampanaDeleteView(CheckEstadoCampanaMixin, DeleteView):
#     """
#     Esta vista se encarga de la eliminación del
#     objeto Actuación seleccionado.
#     """
# 
#     model = Actuacion
#     template_name = 'campana/elimina_actuacion_campana.html'
# 
#     # @@@@@@@@@@@@@@@@@@@@
# 
#     def get_object(self, queryset=None):
#         # FIXME: Esté método no hace nada, se podría remover.
#         actuacion = super(ActuacionCampanaDeleteView, self).get_object(
#             queryset=None)
#         return actuacion
# 
#     def delete(self, request, *args, **kwargs):
#         self.object = self.get_object()
#         success_url = self.get_success_url()
#         self.object.delete()
# 
#         if not self.campana.valida_actuaciones():
#             message = """<strong>¡Cuidado!</strong>
#             Los días del rango de fechas seteados en la campaña NO coinciden
#             con ningún día de las actuaciones programadas. Por consiguiente
#             la campaña NO se ejecutará."""
#             messages.add_message(
#                 self.request,
#                 messages.WARNING,
#                 message,
#             )
# 
#         message = '<strong>Operación Exitosa!</strong>\
#         Se llevó a cabo con éxito la eliminación de la Actuación.'
# 
#         messages.add_message(
#             self.request,
#             messages.SUCCESS,
#             message,
#         )
#         return HttpResponseRedirect(success_url)
# 
#     def get_success_url(self):
#         return reverse(
#             'actuacion_campana',
#             kwargs={"pk_campana": self.campana.pk}
#         )
# 
# 
# class ConfirmaCampanaMixin(object):
# 
#     def post(self, request, *args, **kwargs):
#         self.object = self.get_object()
# 
#         activacion_campana_service = ActivacionCampanaTemplateService()
#         try:
#             activacion_campana_service.activar(self.object)
#         except ValidarCampanaError, e:
#             message = ("<strong>Operación Errónea!</strong> "
#                        "No se pudo confirmar la creación de la campaña debido "
#                        "al siguiente error: {0}".format(e))
#             messages.add_message(
#                 self.request,
#                 messages.ERROR,
#                 message,
#             )
#             return self.render_to_response(self.get_context_data())
#         except RestablecerDialplanError, e:
#             self.object.pausar()
# 
#             message = ("<strong>¡Cuidado!</strong> "
#                        "{0} La campaña será pausada.".format(e))
#             messages.add_message(
#                 self.request,
#                 messages.WARNING,
#                 message,
#             )
#             return redirect(self.get_success_url())
#         else:
#             message = ("<strong>Operación Exitosa!</strong> "
#                        "Se llevó a cabo con éxito la creación de la Campaña.")
#             messages.add_message(
#                 self.request,
#                 messages.SUCCESS,
#                 message,
#             )
#             return redirect(self.get_success_url())
# 
#     def get_success_url(self):
#         return reverse('lista_campana')
# 
# 
# class ConfirmaCampanaView(ConfirmaCampanaMixin, CheckEstadoCampanaMixin,
#                           CampanaEnDefinicionMixin, UpdateView):
#     """
#     Esta vista confirma la creación de un objeto
#     Campana. Imprime el resumen del objeto y si
#     es aceptado, cambia el estado del objeto a ACTIVA.
#     Si el objeto ya esta ACTIVA, redirecciona
#     al listado.
#     """
# 
#     template_name = 'campana/confirma_campana.html'
#     model = Campana
#     context_object_name = 'campana'
