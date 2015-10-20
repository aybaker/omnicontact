# -*- coding: utf-8 -*-

from __future__ import unicode_literals


from django.views.generic import DetailView
from django.views.generic.list import ListView

from fts_web.models import CampanaSms

import logging as logging_

logger = logging_.getLogger(__name__)


# =============================================================================
# Campaña SMS
# =============================================================================


class CampanaSmsListView(ListView):
    """
    Esta vista lista los objetos CapanasSms
    diferenciadas por sus estados actuales.
    Pasa un diccionario al template
    con las claves como estados.
    """

    template_name = 'campana_sms/lista_campana_sms.html'
    context_object_name = 'campanas_sms'
    model = CampanaSms

    def get_context_data(self, **kwargs):
        context = super(CampanaSmsListView, self).get_context_data(
           **kwargs)
        context['confirmadas'] = CampanaSms.objects.obtener_confirmadas()
        context['pausadas'] = CampanaSms.objects.obtener_pausadas()
        return context


class DetalleCampanSmsView(DetailView):
    """
    Muestra el detalle de la campaña sms.
    """
    template_name = 'campana_sms/detalle_campana_sms.html'
    context_object_name = 'campana_sms'
    pk_url_kwarg = 'pk_campana_sms'
    model = CampanaSms

    def dispatch(self, request, *args, **kwargs):
        self.campana_sms = \
            CampanaSms.objects.obtener_para_detalle(kwargs['pk_campana_sms'])
        return super(DetalleCampanSmsView, self).dispatch(request, *args,
                                                       **kwargs)

    def get_object(self, queryset=None):
        return CampanaSms.objects.obtener_para_detalle(
            self.kwargs['pk_campana_sms'])


# class CampanaDeleteView(DeleteView):
#     """
#     Esta vista se encarga de la eliminación del
#     objeto Campana.
#     """
# 
#     model = Campana
#     template_name = 'campana/elimina_campana.html'
# 
#     # @@@@@@@@@@@@@@@@@@@@
# 
#     def dispatch(self, request, *args, **kwargs):
#         self.campana = \
#             Campana.objects.obtener_depurada_para_eliminar(
#                 kwargs['pk_campana'])
#         return super(CampanaDeleteView, self).dispatch(request, *args,
#                                                        **kwargs)
# 
#     def get_object(self, queryset=None):
#         return Campana.objects.obtener_depurada_para_eliminar(
#             self.kwargs['pk_campana'])
# 
#     def delete(self, request, *args, **kwargs):
#         self.object = self.get_object()
#         success_url = self.get_success_url()
# 
#         # Marcamos la campaña como borrada. Lo hacemos primero para que,
#         # en caso de error, la excepcion se lance lo antes posible
#         self.object.borrar()
# 
#         # Eliminamos la tabla generada en la depuración de la campaña.
#         from fts_daemon.models import EventoDeContacto
#         EventoDeContacto.objects.eliminar_tabla_eventos_de_contacto_depurada(
#             self.object)
# 
#         message = '<strong>Operación Exitosa!</strong>\
#         Se llevó a cabo con éxito la eliminación de la Campaña.'
# 
#         messages.add_message(
#             self.request,
#             messages.SUCCESS,
#             message,
#         )
#         return HttpResponseRedirect(success_url)
# 
#     def get_success_url(self):
#         return reverse('lista_campana')
