# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from django.http.response import HttpResponse, HttpResponseServerError
from fts_daemon.models import EventoDeContacto
import logging as logging_


logger = logging_.getLogger(__name__)


#==============================================================================
# AGI
#==============================================================================

def handle_agi_proxy_request(request, agi_network_script):
    logger.info("handle_agi_proxy_request(): '%s'", agi_network_script)

    splitted = agi_network_script.split("/")
    if splitted[-1] == '':
        # si 'agi_network_script' finaliza en '/', el último elemento es vacio
        splitted[0:-1]

    if len(splitted) < 3:
        logger.error("handle_agi_proxy_request(): el request '%s' "
            "posee menos de 3 elementos")

    campana_id = splitted[0]
    contacto_id = splitted[1]
    evento = splitted[2]

    #
    # Intentamos convertir ints
    #

    try:
        campana_id = int(campana_id)
    except ValueError:
        logger.exception("Error al convertir campana_id a entero. "
            "agi_network_script: '%s'", agi_network_script)
        return HttpResponseServerError("ERROR,campana_id")

    try:
        contacto_id = int(contacto_id)
    except ValueError:
        logger.exception("Error al convertir contacto_id a entero. "
            "agi_network_script: '%s'", agi_network_script)
        return HttpResponseServerError("ERROR,contacto_id")

    #
    # Procesamos el evento recibido
    #

    logger.info("handle_agi_proxy_request() - campana_id: %s - "
        "contacto_id: %s - evento: %s", campana_id, contacto_id, evento)

    if evento == "local-channel-pre-dial":
        evento_id = EventoDeContacto.objects.dialplan_local_channel_pre_dial(
            campana_id, contacto_id).id
        return HttpResponse("OK,{0}".format(evento_id))

    elif evento == "inicio":
        evento_id = EventoDeContacto.objects.dialplan_campana_iniciado(
            campana_id, contacto_id).id
        return HttpResponse("OK,{0}".format(evento_id))

    elif evento == "fin":
        evento_id = EventoDeContacto.objects.dialplan_campana_finalizado(
            campana_id, contacto_id).id
        return HttpResponse("OK,{0}".format(evento_id))

    elif evento == "opcion":
        if len(splitted) < 4:
            logger.error("handle_agi_proxy_request(): [/opcion/] el "
                "request '%s' posee menos de 4 elementos", agi_network_script)

        try:
            # FIXME: que pasa si usuario presiona '*' o '#'?
            dtmf_number = int(splitted[4])
        except ValueError:
            logger.exception("Error al convertir DTMF a entero. "
                "agi_network_script: '%s'", agi_network_script)
            return HttpResponseServerError("ERROR,opcion_dtmf_invalido")

        evento_id = EventoDeContacto.objects.opcion_seleccionada(
            campana_id, contacto_id, dtmf_number).id
        return HttpResponse("OK,{0}".format(evento_id))

    elif evento == "local-channel-post-dial":
        # splitted[3] -> dial-status
        # splitted[4] -> DIALSTATUS
        if len(splitted) < 5:
            logger.error("handle_agi_proxy_request(): "
                "[/local-channel-post-dial/] el request '%s' posee menos "
                "de 5 elementos", agi_network_script)
            return HttpResponseServerError("ERROR,local-channel-post-dial")

        if splitted[3] != "dial-status":
            logger.error("handle_agi_proxy_request(): "
                "[/local-channel-post-dial/] el request '%s' no posee "
                "el elemento 'dial-status'", agi_network_script)
            return HttpResponseServerError("ERROR,local-channel-post-dial")

        try:
            mapped_ev = EventoDeContacto.DIALSTATUS_MAP[splitted[4].upper()]
        except KeyError:
            mapped_ev = EventoDeContacto.EVENTO_ASTERISK_DIALSTATUS_UNKNOWN
            logger.warn("handle_agi_proxy_request(): "
                "[/local-channel-post-dial/] el request '%s' no posee "
                "un valor de DIALSTATUS reconocido (se guardara evento como"
                "EVENTO_ASTERISK_DIALSTATUS_UNKNOWN", agi_network_script)

        evento_id = EventoDeContacto.objects.dialplan_local_channel_post_dial(
            campana_id, contacto_id, mapped_ev).id
        return HttpResponse("OK,{0}".format(evento_id))

    elif evento == "fin_err_t":
        evento_id = EventoDeContacto.objects.fin_err_t(
            campana_id, contacto_id).id
        return HttpResponse("OK,{0}".format(evento_id))

    elif evento == "fin_err_i":
        evento_id = EventoDeContacto.objects.fin_err_i(
            campana_id, contacto_id).id
        return HttpResponse("OK,{0}".format(evento_id))

    logger.error("handle_agi_proxy_request(): el request '%s' "
        "hace referencia a evento desconocido", agi_network_script)
    return HttpResponseServerError("ERROR,evento-deconocido")

    # {fts_campana_id}/${{FtsDaemonCallId}}/local-channel-pre-dial/)
    # {fts_campana_id}/${{FtsDaemonCallId}}/local-channel-post-dial/
    #     dial-status/${{DIALSTATUS}}/)
    # {fts_campana_id}/${{FtsDaemonCallId}}/inicio/)
    # {fts_campana_id}/${{FtsDaemonCallId}}/fin/)

    # {fts_campana_id}/${{FtsDaemonCallId}}/opcion/
    #    {fts_opcion_digito}/{fts_opcion_id}/repetir/)
    # {fts_campana_id}/${{FtsDaemonCallId}}/opcion/
    #    {fts_opcion_digito}/{fts_opcion_id}/derivar/)
    # {fts_campana_id}/${{FtsDaemonCallId}}/opcion/
    #    {fts_opcion_digito}/{fts_opcion_id}/calificar/{fts_calificacion_id}/)
    # {fts_campana_id}/${{FtsDaemonCallId}}/opcion/
    #    {fts_opcion_digito}/{fts_opcion_id}/voicemail/)

    # {fts_campana_id}/${{FtsDaemonCallId}}/fin_err/t/)
    # {fts_campana_id}/${{FtsDaemonCallId}}/fin_err/i/)
