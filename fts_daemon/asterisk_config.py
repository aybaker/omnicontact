# -*- coding: utf-8 -*-

"""
Genera archivos de configuración para Asterisk: dialplan y queues.
"""

from __future__ import unicode_literals

import datetime
import os
import shutil
import subprocess
import tempfile
import traceback

from django.conf import settings

from fts_web.models import Campana, GrupoAtencion
import logging as _logging
from fts_daemon.asterisk_config_generador_de_partes import (
    GeneradorDePedazoDeDialplanFactory,
    GeneradorDePedazoDeQueueFactory)
from ominicontacto_app.asterisk_config import AsteriskConfigReloader


logger = _logging.getLogger(__name__)

# def _safe(value):
#    """Limpia texto usado para generar archivo de configuracion"""
#    # FIXME: IMPLEMENTAR y usarlo!
#    # TODO: ver si django no tiene algo armado
#    return value


# TODO: Las siguientes funciones deberán ser removidas en la medida que se
# implemente el uso de los objetos que las reemplazan.


def generar_dialplan(campana):
    dialplan_config_creator = DialplanConfigCreator()
    return dialplan_config_creator._generar_dialplan(campana)


def create_dialplan_config_file(campana=None, campanas=None):
    dialplan_config_creator = DialplanConfigCreator()
    dialplan_config_creator.create_dialplan(campana, campanas)


def generar_queue(grupo_atencion):
    queue_config_creator = QueueConfigCreator()
    return queue_config_creator._generar_queue(grupo_atencion)


def create_queue_config_file():
    queue_config_creator = QueueConfigCreator()
    queue_config_creator.create_queue()


def reload_config():
    reload_asterisk_config = AsteriskConfigReloader()
    return reload_asterisk_config.reload_config()


##############################################################################


class DialplanConfigCreator(object):

    def __init__(self):
        self._dialplan_config_file = DialplanConfigFile()
        self._generador_factory = GeneradorDePedazoDeDialplanFactory()

    def _generar_dialplan(self, campana):
        """Genera el dialplan para una campaña.

        :param campana: Campana para la cual hay crear el dialplan
        :type campana: fts_web.models.Campana
        :returns: str -- dialplan para la campaña
        :raises: Exception en caso de problemas (ej: no se encuentra
            el archivo de audio)
        """

        assert campana is not None, "Campana == None"
        assert campana.estado != Campana.ESTADO_EN_DEFINICION, \
            "Campana: estado == ESTADO_EN_DEFINICION "
        assert campana.id is not None, "campana.id == None"
        assert campana.segundos_ring is not None

        # Chequeamos que se haya seteado al menos un objeto AudioDeCampana.
        audios_de_campana = campana.audios_de_campana.all()
        assert audios_de_campana, "campana.audios_de_campana -> None"

        partes = []
        param_generales = {
            'fts_campana_id': campana.id,
            'fts_campana_dial_timeout': campana.segundos_ring,
            'fts_agi_server': settings.FTS_AGI_DAEMON_HOST,
            'fts_dial_url': settings.ASTERISK['DIAL_URL'],
            'date': str(datetime.datetime.now())
        }

        # START: Creamos la porción inicial del Dialplan.
        generador_start = self._generador_factory.crear_generador_para_start(
            campana, param_generales)
        partes.append(generador_start.generar_pedazo())

        # AUDIOS: Creamos las porciones de los audios del Dialplan.
        for audio_de_campana in audios_de_campana:
            generador = self._generador_factory.crear_generador_para_audio(
                audio_de_campana, param_generales, campana)
            partes.append(generador.generar_pedazo())

        # HANGUP: Creamos la porción para el hangup del Dialplan.
        generador_hangup = self._generador_factory.crear_generador_para_hangup(
            param_generales)
        partes.append(generador_hangup.generar_pedazo())

        # TODO: derivacion: setear GrupoAtencion / QUEUE (cuando corresponda)
        # TODO: voicemail: IMPLEMENTAR!

        # OPCIONES: Creamos las porciones de las opciones del Dialplan.
        for opcion in campana.opciones.all():
            params_opcion = dict(param_generales)
            params_opcion.update({
                'fts_opcion_id': opcion.id,
                'fts_opcion_digito': opcion.digito,
            })

            generador_dialplan = \
                self._generador_factory.crear_generador_para_opcion(
                    opcion, params_opcion, campana)

            partes.append(generador_dialplan.generar_pedazo())

        # END: Creamos la porción para el hangup del Dialplan.
        generador_end = self._generador_factory.crear_generador_para_end(
            param_generales)
        partes.append(generador_end.generar_pedazo())

        return ''.join(partes)

    def _obtener_todas_para_generar_dialplan(self):
        """Devuelve las campanas para crear el dialplan.
        """
        return Campana.objects.obtener_todas_para_generar_dialplan()

    def create_dialplan(self, campana=None, campanas=None):
        """Crea el archivo de dialplan para campanas existentes
        (si `campana` es None). Si `campana` es pasada por parametro,
        se genera solo para dicha campana.
        """

        if campanas:
            pass
        elif campana:
            campanas = [campana]
        else:
            campanas = self._obtener_todas_para_generar_dialplan()
        dialplan = []
        for campana in campanas:
            logger.info("Creando dialplan para campana %s", campana.id)
            try:
                config_chunk = self._generar_dialplan(campana)
                logger.info("Dialplan generado OK para campana %s",
                            campana.id)
            except:
                logger.exception(
                    "No se pudo generar configuracion de "
                    "Asterisk para la campana {0}".format(campana.id))

                try:
                    traceback_lines = [
                        "; {0}".format(line)
                        for line in traceback.format_exc().splitlines()]
                    traceback_lines = "\n".join(traceback_lines)
                except:
                    traceback_lines = "Error al intentar generar traceback"
                    logger.exception("Error al intentar generar traceback")

                # FAILED: Creamos la porción para el fallo del Dialplan.
                param_failed = {'fts_campana_id': campana.id,
                                'date': str(datetime.datetime.now()),
                                'traceback_lines': traceback_lines}
                generador_failed = \
                    self._generador_factory.crear_generador_para_failed(
                        param_failed)
                config_chunk = generador_failed.generar_pedazo()

            dialplan.append(config_chunk)

        self._dialplan_config_file.write(dialplan)


class QueueConfigCreator(object):
    def __init__(self):
        self._queue_config_file = QueueConfigFile()
        self._generador_factory = GeneradorDePedazoDeQueueFactory()

    def _generar_queue(self, grupo_atencion):
        """Genera configuracion para queue / grupos de atencion"""

        partes = []
        param_generales = {
            'fts_grupo_atencion_id': grupo_atencion.id,
            'fts_grupo_atencion_nombre': grupo_atencion.nombre,
            'fts_queue_name': grupo_atencion.get_nombre_para_asterisk(),
            'fts_strategy': grupo_atencion.get_ring_strategy_para_asterisk(),
            'fts_timeout': grupo_atencion.timeout,
            'date': str(datetime.datetime.now())
        }

        # QUEUE: Creamos la porción inicial del Queue.
        generador_queue = self._generador_factory.crear_generador_para_queue(
            param_generales)
        partes.append(generador_queue.generar_pedazo())

        # MEMBER: Creamos la porción inicial del Queue.
        for agente in grupo_atencion.agentes.all():
            generador_member = \
                self._generador_factory.crear_generador_para_member(
                    agente, param_generales)
            partes.append(generador_member.generar_pedazo())

        return ''.join(partes)

    def _obtener_ga_generar_config(self):
        """Devuelve los GA a tener en cuenta para generar el archivo
        de configuracion
        """
        return GrupoAtencion.objects.obtener_todos_para_generar_config()

    def create_queue(self):
        """Crea el archivo de queue para G.A. existentes"""

        grupos_atencion = self._obtener_ga_generar_config()

        queue = []
        for ga in grupos_atencion:
            logger.info("Creando config para grupo de atencion %s", ga.id)
            config_chunk = self._generar_queue(ga)
            queue.append(config_chunk)

        self._queue_config_file.write(queue)


class ConfigFile(object):
    def __init__(self, filename):
        self._filename = filename

    def write(self, contenidos):
        tmp_fd, tmp_filename = tempfile.mkstemp()
        try:
            tmp_file_obj = os.fdopen(tmp_fd, 'w')
            for contenido in contenidos:
                assert isinstance(contenido, unicode), \
                    "Objeto NO es unicode: {0}".format(type(contenido))
                tmp_file_obj.write(contenido.encode('utf-8'))

            tmp_file_obj.close()

            logger.info("Copiando file config a %s", self._filename)
            shutil.copy(tmp_filename, self._filename)
            os.chmod(self._filename, 0644)

        finally:
            try:
                os.remove(tmp_filename)
            except:
                logger.exception("Error al intentar borrar temporal %s",
                                 tmp_filename)


class QueueConfigFile(ConfigFile):
    def __init__(self):
        filename = settings.FTS_QUEUE_FILENAME.strip()
        super(QueueConfigFile, self).__init__(filename)


class DialplanConfigFile(ConfigFile):
    def __init__(self):
        filename = settings.FTS_DIALPLAN_FILENAME.strip()
        super(DialplanConfigFile, self).__init__(filename)