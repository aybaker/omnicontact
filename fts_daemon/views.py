# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from django.http.response import HttpResponse, HttpResponseServerError
from fts_daemon.models import EventoDeContacto
import logging as logging_


logger = logging_.getLogger(__name__)


#==============================================================================
# AGI
#==============================================================================

def local_channel_pre_dial(request, campana_id, contacto_id, intento):
    campana_id = int(campana_id)
    contacto_id = int(contacto_id)
    intento = int(intento)

    evento_id = EventoDeContacto.objects.dialplan_local_channel_pre_dial(
        campana_id, contacto_id, intento).id
    return HttpResponse("OK,{0}".format(evento_id))


def inicio_campana(request, campana_id, contacto_id, intento):
    campana_id = int(campana_id)
    contacto_id = int(contacto_id)
    intento = int(intento)

    evento_id = EventoDeContacto.objects.dialplan_campana_iniciado(
        campana_id, contacto_id, intento).id
    return HttpResponse("OK,{0}".format(evento_id))


def fin_campana(request, campana_id, contacto_id, intento):
    campana_id = int(campana_id)
    contacto_id = int(contacto_id)
    intento = int(intento)

    evento_id = EventoDeContacto.objects.dialplan_campana_finalizado(
        campana_id, contacto_id, intento).id
    return HttpResponse("OK,{0}".format(evento_id))


def fin_err_t(request, campana_id, contacto_id, intento):
    campana_id = int(campana_id)
    contacto_id = int(contacto_id)
    intento = int(intento)

    evento_id = EventoDeContacto.objects.fin_err_t(
        campana_id, contacto_id, intento).id
    return HttpResponse("OK,{0}".format(evento_id))


def fin_err_i(request, campana_id, contacto_id, intento):
    campana_id = int(campana_id)
    contacto_id = int(contacto_id)
    intento = int(intento)

    evento_id = EventoDeContacto.objects.fin_err_i(
        campana_id, contacto_id, intento).id
    return HttpResponse("OK,{0}".format(evento_id))


def opcion_seleccionada(request, campana_id, contacto_id, intento,
    dtmf_number):

    campana_id = int(campana_id)
    contacto_id = int(contacto_id)
    intento = int(intento)

    try:
        # TODO: que pasa si usuario presiona '*' o '#'?
        # de cualquier manera, no lo soportamos por ahora...
        dtmf_number = int(dtmf_number)
    except ValueError:
        logger.exception("Error al convertir DTMF a entero: '{0}'".format(
            dtmf_number))
        return HttpResponseServerError("ERROR,opcion_dtmf_invalido")

    try:
        evento = EventoDeContacto.NUMERO_OPCION_MAP[dtmf_number]
    except KeyError:
        logger.exception("No existe evento para el dtmf '{0}'".format(
            dtmf_number))
        return HttpResponseServerError("ERROR,opcion_dtmf_invalido")

    evento_id = EventoDeContacto.objects.opcion_seleccionada(
        campana_id, contacto_id, intento, evento).id
    return HttpResponse("OK,{0}".format(evento_id))


def local_channel_post_dial(request, campana_id, contacto_id, intento,
    dial_status):

    campana_id = int(campana_id)
    contacto_id = int(contacto_id)
    intento = int(intento)

    try:
        mapped_ev = EventoDeContacto.DIALSTATUS_MAP[dial_status]
        response_status = "OK"
    except KeyError:
        mapped_ev = EventoDeContacto.EVENTO_ASTERISK_DIALSTATUS_UNKNOWN
        response_status = "WARN"
        logger.warn("local_channel_post_dial(): valor de DIALSTATUS "
            "desconocido: '%s' (se guardara evento como"
            "EVENTO_ASTERISK_DIALSTATUS_UNKNOWN", dial_status)

    evento_id = EventoDeContacto.objects.dialplan_local_channel_post_dial(
        campana_id, contacto_id, intento, mapped_ev).id
    return HttpResponse("{0},{1}".format(response_status, evento_id))


def handle_agi_proxy_request(request, agi_network_script):
    logger.error("handle_agi_proxy_request(): el request '%s' "
        "hace referencia a evento desconocido", agi_network_script)
    return HttpResponseServerError("ERROR,evento-deconocido")
