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


class CancelLoop(Exception):
    """Excepcion usada para cancelar loop externo"""
    pass


class Llamador(object):

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

    def run(self, max_loops=0):
        current_loop = 1
        for campana, id_contacto, numero in self._pendientes():
            logger.debug("loop(): campana: %s - id_contacto: %s - numero: %s",
                campana, id_contacto, numero)
            procesar_contacto(campana, id_contacto, numero)

            current_loop += 1
            if max_loops > 0 and current_loop > max_loops:
                logger.info("max_loops alcanzado... saliendo...")
                return


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
    FTS_MAX_LOOPS = int(os.environ.get("FTS_MAX_LOOPS", "0"))
    Llamador().run(max_loops=FTS_MAX_LOOPS)


if __name__ == '__main__':
    main()
