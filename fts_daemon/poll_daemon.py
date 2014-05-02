# -*- coding: utf-8 -*-
'''
Created on Mar 27, 2014

@author: Horacio G. de Oro
'''

from __future__ import unicode_literals

import datetime
import os
import time

from django.conf import settings
from fts_daemon.asterisk_ami_http import AsteriskHttpOriginateError
from fts_web.models import Campana, EventoDeContacto, Contacto
from fts_web.utiles import get_class
import logging as _logging


#
# Import settings & models ^ALLA ARRIBA^ to force setup of Django
#
# Seteamos nombre, sino al ser ejecutado via uWSGI
#  el logger se llamara '__main__'
logger = _logging.getLogger('fts_daemon.poll_daemon')


#class Tracker(object):
#
#    def __init__(self, campana):
#        self._campana = campana
#        self._valido = True
#
#    @property
#    def campana(self):
#        return self._campana
#
#    @property
#    def valido(self):
#        """Un tracker es valido mientras deba ser tenido en cuenta
#        para realizar llamadas.
#
#        Deja de ser valido cuando:
#        1. la fecha actual esta fuera del rango de fechas de la campana
#        2. la hora actual esta fuera del rango de actuaciones
#        3. la campana esta paudada
#        """
#        return self._valido
#
#    def invalidar(self):
#        self._valido = False
#
#    def get_contacto(self):
#        pass


class Llamador(object):
    """Clase base para implementar el llamador"""

    def loop(self):
        raise NotImplementedError()

    def run(self):
        while True:
            self.loop()


class CancelLoop(Exception):
    pass


class LlamadorGenerador(Llamador):

    def _pendientes(self):
        """Generador, devuelve datos para realizar llamadas"""

        while True:
            for campana in Campana.objects.obtener_ejecucion():
                logger.info("Iniciando procesado de campana %s", campana.id)

                # Chequeamos actuacion
                actuacion = campana.obtener_actuacion_actual()
                if not actuacion:
                    logger.info("Cancelando xq no hay actuacion activa para "
                        "campana %s", campana.id)
                    continue

                #
                # Busca pendientes de campana siendo procesada y arranca
                #

                try:
                    pendientes = EventoDeContacto.objects_gestion_llamadas.\
                        obtener_pendientes(campana.id, 10)
                    for pendiente in pendientes:

                        # Fecha actual local.
                        hoy_ahora = datetime.datetime.now()

                        # Esto quiza no haga falta, porque en teoria
                        # el siguiente control de actuacion detectara el
                        # cambio de dia, igual hacemos este re-control
                        if not campana.verifica_fecha(hoy_ahora):
                            raise CancelLoop()

                        if not actuacion.verifica_actuacion(hoy_ahora):
                            raise CancelLoop()

                        # Valida que la campana no se haya pausado.
                        if Campana.objects.verifica_estado_pausada(campana.pk):
                            raise CancelLoop()

                        # Todo está OK. Generamos datos.
                        id_contacto = pendiente[1]
                        contacto = Contacto.objects.get(pk=id_contacto)
                        yield campana, id_contacto, contacto.telefono

                except CancelLoop:
                    pass

            else:
                logger.debug("No hay campanas en ejecucion. Esperaremos...")
                time.sleep(2)

    def loop(self, max_loops=0):
        current_loop = 1
        for campana, id_contacto, numero in self._pendientes():
            logger.debug("loop(): campana: %s - id_contacto: %s - numero: %s",
                campana, id_contacto, numero)
            procesar_contacto(campana, id_contacto, numero)

            current_loop += 1
            if max_loops > 0 and current_loop > max_loops:
                logger.info("max_loops alcanzado... saliendo...")
                return


#class LlamadorPoll(Llamador):
#
#    def __init__(self):
#        self._trackers = dict()
#
#    def _refrescar_trackers(self):
#        """Refresca la lista de self._trackers, si corresponde"""
#
#        for invalidado in ........
#
#        old_trackers = dict(self._trackers) # asi no tocamos `self._trackers`
#        new_trackers = dict()
#
#        for campana in Campana.objects.obtener_ejecucion():
#            if campana in old_trackers:
#                logger.info("Campana %s ya esta siendo trackeada", campana.id)
#                new_trackers[campana] = old_trackers[campana]
#                del old_trackers[campana]
#            else:
#                logger.info("Se comenzara a trackear Campana %s", campana.id)
#                new_trackers[campana] = Tracker(campana)
#
#        for campana in old_trackers:
#            logger.info("Dejando de trackear Campana %s", campana.id)
#
#        # Y seteamos el nuevo dict de trackers
#        self._trackers = new_trackers
#
#    def loop(self):
#        # Refrescamos si correspodne
#        self._refrescar_trackers()
#
#        # Iteramos copia, para poder eliminar camanas q' ya no estan en curso
#        for campana, tracker in self._trackers:
#
#            # Chequeamos actuacion
#            actuacion = campana.obtener_actuacion_actual()
#            if not actuacion:
#                tracker.invalidar()
#                continue


#def procesar_campana(campana):
#    """Procesa una campana (no chequea su estado, se suponque que
#    la campaña esta en el estado correcto).
#
#    El procesado incluye: buscar intentos de envios pendientes e
#    intentar la llamadas.
#
#    Una vez que se procesaro tondos los intentos pendientes, se
#    marca la campaña como finalizada.
#
#    Returns:
#        cant_contactos_procesados
#    """
#    assert isinstance(campana, Campana)
#    logger.info("Iniciando procesado de campana %s", campana.id)
#    contador_contactos = 0
#
#    actuacion = campana.obtener_actuacion_actual()
#    if not actuacion:
#        return contador_contactos
#
#    for pendiente in campana.obtener_intentos_pendientes():
#        # Fecha actual local.
#        hoy_ahora = datetime.datetime.now()
#
#        # Esto quiza no haga falta, porque en teoria
#        # el siguiente control de actuacion detectara el
#        # cambio de dia, igual hacemos este re-control
#        if not campana.verifica_fecha(hoy_ahora):
#            return contador_contactos
#
#        if not actuacion.verifica_actuacion(hoy_ahora):
#            return contador_contactos
#
#        # Valida que la campana no se haya pausado.
#        if Campana.objects.verifica_estado_pausada(campana.pk):
#            return contador_contactos
#
#        procesar_contacto(pendiente, campana)
#        contador_contactos += 1
#    else:
#        logger.info("Marcando campana %s como FINALIZADA", campana.id)
#        campana.finalizar()
#
#    return contador_contactos


def procesar_contacto(campana, contacto_id, numero):
    """Intenta contactar"""

    logger.info("Realizando originate - campana: %s - contacto: %s",
        campana.id, contacto_id)

    EventoDeContacto.objects.inicia_intento(campana.id, contacto_id)

    # Local/{contactoId}-{numberToCall}@FTS_local_campana_{campanaId}
    channel = settings.ASTERISK['LOCAL_CHANNEL'].format(
        contactoId=str(contacto_id),
        numberToCall=str(numero),
        campanaId=str(campana.id),
    )
    context = campana.get_nombre_contexto_para_asterisk()
    exten = settings.ASTERISK['EXTEN'].format(
        contactoId=str(contacto_id),
    )

    http_client_clazz = get_class(settings.FTS_ASTERISK_HTTP_CLIENT)
    http_ami_client = http_client_clazz()

    try:
        http_ami_client.login()
        http_ami_client.originate(channel, context, exten, 1,
            (campana.segundos_ring + 2) * 1000, async=True)
        EventoDeContacto.objects.\
            create_evento_daemon_originate_successful(
                campana.id, contacto_id)
    except AsteriskHttpOriginateError:
        logger.exception("Originate failed - campana: %s - contacto: %s",
            campana.id, contacto_id)
        EventoDeContacto.objects.\
            create_evento_daemon_originate_failed(
                campana.id, contacto_id)
    except:
        logger.exception("Originate failed - campana: %s - contacto: %s",
            campana.id, contacto_id)
        EventoDeContacto.objects.\
            create_evento_daemon_originate_internal_error(
                campana.id, contacto_id)


def main():
    logger.info("Iniciando loop: obteniendo campanas activas...")
    #while True:
    #    campanas = Campana.objects.obtener_ejecucion()
    #    for campana in campanas:
    #        procesar_campana(campana)
    #    time.sleep(2)
    FTS_MAX_LOOPS = int(os.environ.get("FTS_MAX_LOOPS", "0"))
    LlamadorGenerador().loop(max_loops=FTS_MAX_LOOPS)


if __name__ == '__main__':
    main()
