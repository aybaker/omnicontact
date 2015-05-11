# -*- coding: utf-8 -*-
"""
"""

from __future__ import unicode_literals

import logging
import os
import random

from django.conf import settings
from django.http.response import HttpResponse, HttpResponseServerError
from django.template.context import Context
from django.template.loader import get_template_from_string
from fts_daemon.asterisk_ami_http import AmiStatusTracker
from fts_daemon.models import EventoDeContacto


logger = logging.getLogger(__name__)


def _read(filename):
    view_dir = os.path.dirname(__file__)
    resources_dir = os.path.join(view_dir, 'resources')
    abs_filename = os.path.join(resources_dir, filename)
    assert os.path.exists(abs_filename)
    with open(abs_filename, 'r') as f:
        return f.read()


def _custom_status():
    # Local/{contact_id}-{numero}@FTS_local_campana_{campana_id}-xxx
    template = get_template_from_string(_read("mxml-status-con-llamadas"
        "-en-local-channel-TEMPLATE.xml"))
    ctx = Context(dict(custom_status_values=settings.CUSTOM_STATUS_VALUES))
    return template.render(ctx)


def mxml(request, code):

    action = request.GET.get('action', '')

    # Permission denied
    # Esto tiene prioridad. Si code == 'permission-denied',
    # se devuelve este xml para todos los comandos
    if code == 'permission-denied':
        return HttpResponse(_read(
            'mxml-permission-denied.xml'))

    # Login
    if action == 'login':
        if code == 'login-ok':
            return HttpResponse(_read(
                'mxml-login-success-authentication-accepted.xml'))
        if code == 'login-auth-failed':
            return HttpResponse(_read(
                'mxml-login-authentication-failed.xml'))
        # default
        return HttpResponse(_read(
            'mxml-login-success-authentication-accepted.xml'))

    # Ping
    if action == 'ping':
        if code == 'ping-ok':
            return HttpResponse(_read(
                'mxml-ping-ok.xml'))
        # default
        return HttpResponse(_read(
            'mxml-ping-ok.xml'))

    # Status
    if action == 'status':
        if code == 'status-con-local-channel':
            return HttpResponse(_read(
                'mxml-status-con-llamadas-en-local-channel.xml'))
        if code == 'status-1-llamada':
            return HttpResponse(_read(
                'mxml-status-con-1-llamada.xml'))
        if code == 'status-sin-llamadas':
            return HttpResponse(_read(
                'mxml-status-sin-llamados.xml'))
        if code == 'status-ringing':
            return HttpResponse(_read(
                'mxml-status-ringing.xml'))
        if code == 'status-muchas-llamadas':
            return HttpResponse(_read(
                'mxml-status-con-muchas-llamadas.xml'))
        if code == 'status-muchas-llamadas-4-campanas':
            return HttpResponse(_read(
                'mxml-status-con-muchas-llamadas-4-campanas.xml'))
        if code == 'status-muchas-1-llamada-en-local-channel-ringing':
            return HttpResponse(_read(
                'mxml-status-con-1-llamada-en-local-channel-ringing.xml'))
        if code == 'status-con-1-llamada-en-channel-no-local':
            return HttpResponse(_read(
                'mxml-status-con-1-llamada-en-channel-no-local.xml'))
        if code == 'status-llamada-en-local-channel-CUSTOM':
            return HttpResponse(_custom_status())
        # default
        return HttpResponse(_read(
            'mxml-status-sin-llamados.xml'))

    # Originate
    if action == 'originate':
        if code == 'originate-failed-exten-not-exists':
            return HttpResponse(_read(
                'mxml-originate-failed-extension-does-not-exists.xml'))
        if code == 'originate-failed':
            return HttpResponse(_read(
                'mxml-originate-failed.xml'))
        if code == 'originate-ok':
            return HttpResponse(_read(
                'mxml-originate-ok.xml'))
        # default
        return HttpResponse(_read(
            'mxml-originate-ok.xml'))

    logging.error("action desconocido: {0}".format(action))
    return HttpResponseServerError(
        "action desconocido: {0}".format(action))


#==============================================================================
# Eventos
#==============================================================================

# EventoDeContacto.EVENTO_CONTACTO_PROGRAMADO,
# EventoDeContacto.EVENTO_DAEMON_INICIA_INTENTO,
# EventoDeContacto.EVENTO_DAEMON_ORIGINATE_SUCCESSFUL,
# EventoDeContacto.EVENTO_DAEMON_ORIGINATE_FAILED,
# EventoDeContacto.EVENTO_DAEMON_ORIGINATE_INTERNAL_ERROR,
# EventoDeContacto.EVENTO_ASTERISK_DIALPLAN_LOCAL_CHANNEL_INICIADO,

OPCIONES = []
#opciones += [
#    EventoDeContacto.EVENTO_ASTERISK_DIALPLAN_CAMPANA_INICIADO,
#    EventoDeContacto.EVENTO_ASTERISK_DIALPLAN_CAMPANA_FINALIZADO,
#]

OPCIONES += [
    EventoDeContacto.EVENTO_ASTERISK_DIALPLAN_CAMPANA_ERR_T,
    EventoDeContacto.EVENTO_ASTERISK_DIALPLAN_CAMPANA_ERR_I,
]

OPCIONES += [
    EventoDeContacto.EVENTO_ASTERISK_DIALSTATUS_ANSWER,
    EventoDeContacto.EVENTO_ASTERISK_DIALSTATUS_BUSY,
    EventoDeContacto.EVENTO_ASTERISK_DIALSTATUS_NOANSWER,
    EventoDeContacto.EVENTO_ASTERISK_DIALSTATUS_CANCEL,
    EventoDeContacto.EVENTO_ASTERISK_DIALSTATUS_CONGESTION,
    EventoDeContacto.EVENTO_ASTERISK_DIALSTATUS_CHANUNAVAIL,
    EventoDeContacto.EVENTO_ASTERISK_DIALSTATUS_DONTCALL,
    EventoDeContacto.EVENTO_ASTERISK_DIALSTATUS_TORTURE,
    EventoDeContacto.EVENTO_ASTERISK_DIALSTATUS_INVALIDARGS,
    EventoDeContacto.EVENTO_ASTERISK_DIALSTATUS_UNKNOWN,
] * 5

OPCIONES += [
    EventoDeContacto.EVENTO_ASTERISK_OPCION_0,
    EventoDeContacto.EVENTO_ASTERISK_OPCION_1,
    EventoDeContacto.EVENTO_ASTERISK_OPCION_2,
    EventoDeContacto.EVENTO_ASTERISK_OPCION_3,
    EventoDeContacto.EVENTO_ASTERISK_OPCION_4,
    EventoDeContacto.EVENTO_ASTERISK_OPCION_5,
    EventoDeContacto.EVENTO_ASTERISK_OPCION_6,
    EventoDeContacto.EVENTO_ASTERISK_OPCION_7,
    EventoDeContacto.EVENTO_ASTERISK_OPCION_8,
    EventoDeContacto.EVENTO_ASTERISK_OPCION_9,
] * 20


def simulador(request):
    """Si el request es por un ORIGINATE, ademas de simular su ejecucion,
    inserta eventos de forma aleatorioa en la BD, para simular que
    la llamada se produjo
    """

    SIMULADOR_PROBABILIDAD_NO_RESPONDIO = 0.2

    SIMULADOR_PROBABILIDAD_NO_ELIGE_OPCION = 0.3

    action = request.GET.get('action', '')

    response = mxml(request, "status-sin-llamadas")

    if action != 'originate':
        return response

    if random.random() < SIMULADOR_PROBABILIDAD_NO_RESPONDIO:
        return response

    # ~~~~~ ORIGINATE ~~~~~

    #'channel':
    #   ANTES: Local/{contactoId}-{numberToCall}@FTS_local_campana_{campanaId}
    #          Local/{contactoId}-{numberToCall}-{intento}@
    #              FTS_local_campana_{campanaId}
    match_obj = AmiStatusTracker().REGEX.match(
        request.GET.get('channel', ''))

    if not match_obj:
        logger.error("NO SE PUDO OBTENER CAMPANA Y CONTACTO DE '%s'",
            request.GET.get('channel', ''))
        return response

    contacto_id = match_obj.group(1)
    # numero = match_obj.group(2)
    intento = match_obj.group(3)
    campana_id = match_obj.group(4)

    # TODO: ver q' nro de intento es, y utilizar ese número, en vez
    #  de siempre "1"

    # Genero evento - DIALPLAN en Local channel
    EventoDeContacto.objects.dialplan_local_channel_pre_dial(
        campana_id, contacto_id, intento)

    # Genero evento - DIALPLAN en CTX de campaña
    EventoDeContacto.objects.dialplan_campana_iniciado(
        campana_id, contacto_id, intento)

    if random.random() < SIMULADOR_PROBABILIDAD_NO_ELIGE_OPCION:
        return response

    evento = random.choice(OPCIONES)
    logger.info("SIMULANDO EVENTO %s para contacto %s para campana %s",
        evento, contacto_id, campana_id)

    EventoDeContacto.objects.create(campana_id=campana_id,
        contacto_id=contacto_id, evento=evento, dato=intento)

    return response
