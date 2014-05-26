# -*- coding: utf-8 -*-

'''
Created on Mar 31, 2014

@author: Horacio G. de Oro
'''

from __future__ import unicode_literals

import re

from fts_daemon.models import EventoDeContacto
import logging as _logging


logger = _logging.getLogger('fts_daemon.fastagi_daemon')


#==============================================================================
# Vistas
#==============================================================================

def local_channel_pre_dial(CONN_POOL, campana_id, contacto_id, intento):
    campana_id = int(campana_id)
    contacto_id = int(contacto_id)
    intento = int(intento)

    ev = EventoDeContacto.EVENTO_ASTERISK_DIALPLAN_LOCAL_CHANNEL_INICIADO
    insert_evento_de_contacto(CONN_POOL, campana_id, contacto_id, ev, intento)
    #    evento_id = EventoDeContacto.objects.dialplan_local_channel_pre_dial(
    #        campana_id, contacto_id, intento).id
    #return "OK,{0}".format(0)


def inicio_campana(CONN_POOL, campana_id, contacto_id, intento):
    campana_id = int(campana_id)
    contacto_id = int(contacto_id)
    intento = int(intento)

    ev = EventoDeContacto.EVENTO_ASTERISK_DIALPLAN_CAMPANA_INICIADO
    insert_evento_de_contacto(CONN_POOL, campana_id, contacto_id, ev, intento)
    #    evento_id = EventoDeContacto.objects.dialplan_campana_iniciado(
    #        campana_id, contacto_id, intento).id
    #return "OK,{0}".format(0)


def fin_campana(CONN_POOL, campana_id, contacto_id, intento):
    campana_id = int(campana_id)
    contacto_id = int(contacto_id)
    intento = int(intento)

    ev = EventoDeContacto.EVENTO_ASTERISK_DIALPLAN_CAMPANA_FINALIZADO
    insert_evento_de_contacto(CONN_POOL, campana_id, contacto_id, ev, intento)
    #    evento_id = EventoDeContacto.objects.dialplan_campana_finalizado(
    #        campana_id, contacto_id, intento).id
    #return "OK,{0}".format(0)


def fin_err_t(CONN_POOL, campana_id, contacto_id, intento):
    campana_id = int(campana_id)
    contacto_id = int(contacto_id)
    intento = int(intento)

    ev = EventoDeContacto.EVENTO_ASTERISK_DIALPLAN_CAMPANA_ERR_T
    insert_evento_de_contacto(CONN_POOL, campana_id, contacto_id, ev, intento)
    #    evento_id = EventoDeContacto.objects.fin_err_t(
    #        campana_id, contacto_id, intento).id
    #return "OK,{0}".format(0)


def fin_err_i(CONN_POOL, campana_id, contacto_id, intento):
    campana_id = int(campana_id)
    contacto_id = int(contacto_id)
    intento = int(intento)

    ev = EventoDeContacto.EVENTO_ASTERISK_DIALPLAN_CAMPANA_ERR_I
    insert_evento_de_contacto(CONN_POOL, campana_id, contacto_id, ev, intento)
    #    evento_id = EventoDeContacto.objects.fin_err_i(
    #        campana_id, contacto_id, intento).id
    #return "OK,{0}".format(0)


def opcion_seleccionada(CONN_POOL, campana_id, contacto_id, intento,
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
        #return "ERROR,opcion_dtmf_invalido"
        return

    try:
        evento = EventoDeContacto.NUMERO_OPCION_MAP[dtmf_number]
    except KeyError:
        logger.exception("No existe evento para el dtmf '{0}'".format(
            dtmf_number))
        #return "ERROR,opcion_dtmf_invalido"
        return

    insert_evento_de_contacto(CONN_POOL, campana_id, contacto_id, evento,
        intento)

    #    evento_id = EventoDeContacto.objects.opcion_seleccionada(
    #        campana_id, contacto_id, intento, evento).id
    #return "OK,{0}".format(0)


def local_channel_post_dial(CONN_POOL, campana_id, contacto_id, intento,
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
            "desconocido: '%s' (se guardara evento como "
            "EVENTO_ASTERISK_DIALSTATUS_UNKNOWN", dial_status)

    insert_evento_de_contacto(CONN_POOL, campana_id, contacto_id, mapped_ev,
        intento)

    #    evento_id = EventoDeContacto.objects.dialplan_local_channel_post_dial(
    #        campana_id, contacto_id, intento, mapped_ev).id
    #return "{0},{1}".format(response_status, 0)


#==============================================================================
# Metodos utilitarios
#==============================================================================

def create_urls():
    """Devuelve listas con expresiones regulares que matechean
    las distintas funciones vistas, ala Django."""
    urls = []
    urls.append((
        '^(?P<campana_id>\d+)/(?P<contacto_id>\d+)/(?P<intento>\d+)'
            '/local-channel-pre-dial/$',
        local_channel_pre_dial
    ))
    urls.append((
        '^(?P<campana_id>\d+)/(?P<contacto_id>\d+)/(?P<intento>\d+)'
            '/inicio/$',
        inicio_campana))
    urls.append((
        '^(?P<campana_id>\d+)/(?P<contacto_id>\d+)/(?P<intento>\d+)'
            '/fin/$',
        fin_campana))
    urls.append((
        '^(?P<campana_id>\d+)/(?P<contacto_id>\d+)/(?P<intento>\d+)'
            '/fin_err_t/$',
        fin_err_t))
    urls.append((
        '^(?P<campana_id>\d+)/(?P<contacto_id>\d+)/(?P<intento>\d+)'
            '/fin_err_i/$',
        fin_err_i))
    urls.append((
        '^(?P<campana_id>\d+)/(?P<contacto_id>\d+)/(?P<intento>\d+)'
            '/opcion/(?P<dtmf_number>\d+)/',
        opcion_seleccionada))
    urls.append((
        '^(?P<campana_id>\d+)/(?P<contacto_id>\d+)/(?P<intento>\d+)'
            '/local-channel-post-dial/dial-status/(?P<dial_status>.+)/$',
        local_channel_post_dial))

    return urls


def create_regex():
    """Genera REGEX a partir de urls, ala Django."""
    regexes = []
    for url, view in create_urls():
        regex = re.compile(url)
        regexes.append([regex, view])
    return regexes


class UrlNoMatcheaNingunaVista(Exception):
    """Representa un fallo en la busqueda de la vista para un
    URL dado
    """
    pass


def get_view(regexes, url):
    """Devuelve vista y `match_object` que matchea `url`, ala Django.
    Genera excepcion si no se encuentra ninguna vista.

    :returns: (view, dict) con vista y argumentos para la vista
    :raises UrlNoMatcheaNingunaVista: si no se encuentra ninguna vista
                                      asociada a la url pasada por
                                      parametro.
    """
    assert regexes
    assert url

    for regex, view in regexes:
        match = regex.match(url)
        if match:
            return view, match.groupdict()

    raise UrlNoMatcheaNingunaVista("No se encontro vista mapeada "
        "a la url {0}".format(url))


def insert_evento_de_contacto(CONN_POOL, campana_id, contacto_id, evento,
    dato):
    """Inserta un EDC en la BD. En caso de error, lo reporta y
    continua. No lanza excepciones.
    """
    conn = None
    try:
        conn = CONN_POOL.getconn()
        if not conn.autocommit:
            conn.autocommit = True
        cur = conn.cursor()
        cur.execute("""INSERT INTO fts_daemon_eventodecontacto
            (campana_id, contacto_id, timestamp, evento, dato)
            VALUES
            (%s, %s, NOW(), %s, %s)
        """, [campana_id, contacto_id, evento, dato])
        logger.info("EDC - Insercion OK - "
            "Campana: %s - Contacto: %s - Evento: %s",
            campana_id, contacto_id, evento)
    except:
        logger.exception("No se pudo insertar evento %s para campana %s "
            "y contacto %s", evento, campana_id, contacto_id)
    finally:
        if conn is not None:
            CONN_POOL.putconn(conn)
