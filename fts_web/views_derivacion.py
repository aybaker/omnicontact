# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from django.contrib import messages
from django.core.urlresolvers import reverse
from django.http.response import HttpResponseRedirect
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.views.generic.list import ListView
from fts_daemon.asterisk_config import create_dialplan_config_file, \
    reload_config
from fts_web.forms import DerivacionExternaForm
from fts_web.models import GrupoAtencion, DerivacionExterna
import logging as logging_


logger = logging_.getLogger(__name__)

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
