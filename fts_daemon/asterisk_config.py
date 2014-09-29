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

from fts_web.errors import FtsError
from fts_web.models import Opcion, Campana, GrupoAtencion
import logging as _logging


logger = _logging.getLogger(__name__)

#def _safe(value):
#    """Limpia texto usado para generar archivo de configuracion"""
#    # FIXME: IMPLEMENTAR y usarlo!
#    # TODO: ver si django no tiene algo armado
#    return value
TEMPLATE_DIALPLAN_START = """

;----------------------------------------------------------------------
; TEMPLATE_DIALPLAN_START-{fts_campana_id}
;   Autogenerado {date}
;----------------------------------------------------------------------

;----------------------------------------------------------------------
; Para usar local channels
;----------------------------------------------------------------------

[FTS_local_campana_{fts_campana_id}]

exten => _X.,1,NoOp(FTS,INICIO,llamada=${{EXTEN}},campana={fts_campana_id})
exten => _X.,n,Set(ContactoId=${{CUT(EXTEN,,1)}})
exten => _X.,n,Set(NumberToCall=${{CUT(EXTEN,,2)}})
exten => _X.,n,Set(Intento=${{CUT(EXTEN,,3)}})
exten => _X.,n,NoOp(FTS,ContactoId=${{ContactoId}},NumberToCall=${{NumberToCall}},Intento=${{Intento}})
exten => _X.,n,AGI(agi://{fts_agi_server}/{fts_campana_id}/${{ContactoId}}/${{Intento}}/local-channel-pre-dial/)
exten => _X.,n,Dial({fts_dial_url},{fts_campana_dial_timeout})
; # TODO: *** WARN: el siguiente 'AGI()' a veces no es llamado
exten => _X.,n,AGI(agi://{fts_agi_server}/{fts_campana_id}/${{ContactoId}}/${{Intento}}/local-channel-post-dial/dial-status/${{DIALSTATUS}}/)
exten => _X.,n,Hangup()

;----------------------------------------------------------------------
; Dialplan de campana (audio, opciones, etc)
;----------------------------------------------------------------------

[campania_{fts_campana_id}]

exten => _ftsX.,1,NoOp(FTS,INICIO,EXTEN=${{EXTEN}},campana={fts_campana_id})
exten => _ftsX.,n,Set(OriginalExten=${{EXTEN}})
exten => _ftsX.,n,Set(ContactoId=${{CUT(EXTEN,,2)}})
exten => _ftsX.,n,Set(NumberToCall=${{CUT(EXTEN,,3)}})
exten => _ftsX.,n,Set(Intento=${{CUT(EXTEN,,4)}})
exten => _ftsX.,n,AGI(agi://{fts_agi_server}/{fts_campana_id}/${{ContactoId}}/${{Intento}}/inicio/)
exten => _ftsX.,n,Wait(1)
exten => _ftsX.,n,Answer()
exten => _ftsX.,n(audio),NoOp()
"""


TEMPLATE_DIALPLAN_PLAY_AUDIO = """
; TEMPLATE_DIALPLAN_PLAY_AUDIO-{fts_audio_de_campana_id}
exten => _ftsX.,n,Background({fts_audio_file})
"""


TEMPLATE_DIALPLAN_TTS = """
; TEMPLATE_DIALPLAN_TTS-{fts_audio_de_campana_id}
exten => _ftsX.,n,NoOp(TTS,{fts_tts},${{{fts_tts}}})
exten => _ftsX.,n,AGI(googletts.agi,${{{fts_tts}}},es)
"""


TEMPLATE_DIALPLAN_HORA = """
; TEMPLATE_DIALPLAN_HORA-{fts_audio_de_campana_id}
exten => _ftsX.,n,NoOp(TTS,{fts_tts_hora}_hora,${{{fts_tts_hora}_hora}})
exten => _ftsX.,n,Saynumber(${{{fts_tts_hora}_hora}})
exten => _ftsX.,n,Playback(horas)
exten => _ftsX.,n,NoOp(TTS,{fts_tts_hora}_min,${{{fts_tts_hora}_min}})
exten => _ftsX.,n,Saynumber(${{{fts_tts_hora}_min}})
exten => _ftsX.,n,Playback(minutos)
"""


TEMPLATE_DIALPLAN_FECHA = """
; TEMPLATE_DIALPLAN_FECHA-{fts_audio_de_campana_id}
exten => _ftsX.,n,NoOp(TTS,{fts_tts_fecha}_dia,${{{fts_tts_fecha}_dia}})
exten => _ftsX.,n,Saynumber(${{{fts_tts_fecha}_dia}})
exten => _ftsX.,n,Playback(del)
exten => _ftsX.,n,NoOp(TTS,{fts_tts_fecha}_mes,${{{fts_tts_fecha}_mes}})
exten => _ftsX.,n,Playback(${{{fts_tts_fecha}_mes}})
exten => _ftsX.,n,Playback(de)
exten => _ftsX.,n,NoOp(TTS,{fts_tts_fecha}_anio,${{{fts_tts_fecha}_anio}})
exten => _ftsX.,n,Saynumber(${{{fts_tts_fecha}_anio}})
"""


TEMPLATE_DIALPLAN_HANGUP = """
; TEMPLATE_DIALPLAN_HANGUP-{fts_campana_id}
; TODO: alcanza 'WaitExten(10)'?
exten => _ftsX.,n,WaitExten(10)
exten => _ftsX.,n,AGI(agi://{fts_agi_server}/{fts_campana_id}/${{ContactoId}}/${{Intento}}/fin/)
exten => _ftsX.,n,Hangup()
"""


TEMPLATE_OPCION_REPETIR = """

; TEMPLATE_OPCION_REPETIR-{fts_opcion_id}
exten => {fts_opcion_digito},1,NoOp(FTS,REPETIR,llamada=${{ContactoId}},campana={fts_campana_id})
exten => {fts_opcion_digito},n,AGI(agi://{fts_agi_server}/{fts_campana_id}/${{ContactoId}}/${{Intento}}/opcion/{fts_opcion_digito}/{fts_opcion_id}/repetir/)
exten => {fts_opcion_digito},n,Goto(${{OriginalExten}},audio)
exten => {fts_opcion_digito},n,Hangup()

"""

TEMPLATE_OPCION_DERIVAR_GRUPO_ATENCION = """

; TEMPLATE_OPCION_DERIVAR_GRUPO_ATENCION-{fts_opcion_id}-{fts_grup_atencion_id}-{fts_queue_name}
exten => {fts_opcion_digito},1,NoOp(FTS,DERIVAR_GRUPO_ATENCION,llamada=${{ContactoId}},campana={fts_campana_id},queue={fts_queue_name})
exten => {fts_opcion_digito},n,AGI(agi://{fts_agi_server}/{fts_campana_id}/${{ContactoId}}/${{Intento}}/opcion/{fts_opcion_digito}/{fts_opcion_id}/derivar/)
exten => {fts_opcion_digito},n,Queue({fts_queue_name})
exten => {fts_opcion_digito},n,Hangup()

"""

TEMPLATE_OPCION_DERIVAR_DERIVACION_EXTERNA = """

; TEMPLATE_OPCION_DERIVAR_DERIVACION_EXTERNA-{fts_opcion_id}-{fts_derivacion_externa_id}-{fts_dial_string}
exten => {fts_opcion_digito},1,NoOp(FTS,DERIVAR_DERIVACION_EXTERNA,llamada=${{ContactoId}},campana={fts_campana_id},dial_string={fts_dial_string})
exten => {fts_opcion_digito},n,AGI(agi://{fts_agi_server}/{fts_campana_id}/${{ContactoId}}/${{Intento}}/opcion/{fts_opcion_digito}/{fts_opcion_id}/derivacion_externa/)
exten => {fts_opcion_digito},n,Dial({fts_dial_string})
exten => {fts_opcion_digito},n,Hangup()

"""

TEMPLATE_OPCION_CALIFICAR = """

; TEMPLATE_OPCION_CALIFICAR-{fts_opcion_id}-{fts_calificacion_id}-{fts_calificacion_nombre}
exten => {fts_opcion_digito},1,NoOp(FTS,CALIFICAR,llamada=${{ContactoId}},campana={fts_campana_id},calificacion={fts_calificacion_id}-fts_calificacion_nombre)
exten => {fts_opcion_digito},n,AGI(agi://{fts_agi_server}/{fts_campana_id}/${{ContactoId}}/${{Intento}}/opcion/{fts_opcion_digito}/{fts_opcion_id}/calificar/{fts_calificacion_id}/)
exten => {fts_opcion_digito},n,Playback(demo-thanks)
exten => {fts_opcion_digito},n,Hangup()

"""

TEMPLATE_OPCION_VOICEMAIL = """

; TEMPLATE_OPCION_VOICEMAIL-{fts_opcion_id}
exten => {fts_opcion_digito},1,NoOp(FTS,VOICEMAIL,llamada=${{ContactoId}},campana={fts_campana_id})
exten => {fts_opcion_digito},n,AGI(agi://{fts_agi_server}/{fts_campana_id}/${{ContactoId}}/${{Intento}}/opcion/{fts_opcion_digito}/{fts_opcion_id}/voicemail/)
exten => {fts_opcion_digito},n,Goto(${{OriginalExten}},audio)
; TODO: IMPLEMENTAR!
exten => {fts_opcion_digito},n,Hangup()

"""

TEMPLATE_DIALPLAN_END = """

; TEMPLATE_DIALPLAN_END-{fts_campana_id}
exten => t,1,NoOp(FTS,ERR_T,llamada=${{ContactoId}},campana={fts_campana_id})
exten => t,n,AGI(agi://{fts_agi_server}/{fts_campana_id}/${{ContactoId}}/${{Intento}}/fin_err_t/)
exten => t,n,Hangup()

exten => i,1,NoOp(FTS,ERR_I,llamada=${{ContactoId}},campana={fts_campana_id})
exten => i,n,AGI(agi://{fts_agi_server}/{fts_campana_id}/${{ContactoId}}/${{Intento}}/fin_err_i/)
exten => i,n,Hangup()

"""

TEMPLATE_FAILED = """

;----------------------------------------------------------------------
; TEMPLATE_FAILED-{fts_campana_id}
;   Autogenerado {date}
;
; La generacion de configuracin para la campana {fts_campana_id}
;   a fallado.
;
; {traceback_lines}
;
;----------------------------------------------------------------------

"""

TEMPLATE_QUEUE = """

;----------------------------------------------------------------------
; TEMPLATE_QUEUE-{fts_queue_name}
;   Autogenerado {date}
;----------------------------------------------------------------------
; Grupo de Atencion
;     - Id: {fts_grupo_atencion_id}
; - Nombre: {fts_grupo_atencion_nombre}
;----------------------------------------------------------------------

[{fts_queue_name}]

strategy={fts_strategy}
timeout={fts_timeout}
maxlen=0
monitor-type=mixmonitor
monitor-format=wav

"""

TEMPLATE_QUEUE_MEMBER = """

; agente.id={fts_agente_id}
member => SIP/{fts_member_number}

"""

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


class NoSePuedeCrearDialplanError(FtsError):
    """Indica que no se pudo crear el dialplan."""
    pass


class DialplanConfigCreator(object):

    def __init__(self):
        self._dialplan_config_file = DialplanConfigFile()

    def _check_audio_file_exist(self, fts_audio_file, campana):
        if not os.path.exists(fts_audio_file):
            raise NoSePuedeCrearDialplanError(
                "No se encontro el archivo de audio '{0}' para la campana "
                "'{1}'".format(fts_audio_file, campana.id))

    def _generar_dialplan(self, campana):
        """Genera el dialplan para una campaña.

        :param campana: Campana para la cual hay crear el dialplan
        :type campana: fts_web.models.Campana
        :returns: str -- dialplan para la campaña
        :raises: Exception en caso de problemas (ej: no se encuentra
            el archivo de audio)
        """

        assert campana is not None, "Campana == None"
        assert campana.estado != Campana.ESTADO_EN_DEFINICION,\
            "Campana: estado == ESTADO_EN_DEFINICION "
        assert campana.id is not None, "campana.id == None"
        assert campana.segundos_ring is not None

        # Chequeamos que se haya seteado al menos un objeto AudioDeCampana.
        audios_de_campana = campana.audios_de_campana.all()
        assert audios_de_campana, "campana.audios_de_campana -> None"

        # Chequeamos que cada objeto, al menos tenga setada uno de los posibles
        # audios.
        for audio_de_campana in audios_de_campana:
            posibles_audios = [audio_de_campana.audio_asterisk,
                               audio_de_campana.archivo_de_audio,
                               audio_de_campana.tts]
            assert any(posibles_audios), "Un AudioDeCampana no es valido."

        partes = []
        param_generales = {
            'fts_campana_id': campana.id,
            'fts_campana_dial_timeout': campana.segundos_ring,
            'fts_agi_server': '127.0.0.1',  # TODO: mover a settings
            'fts_dial_url': settings.ASTERISK['DIAL_URL'],
            'date': str(datetime.datetime.now())
        }

        partes.append(TEMPLATE_DIALPLAN_START.format(**param_generales))

        for audio_de_campana in audios_de_campana:
            if audio_de_campana.audio_asterisk:
                # Un archivo subido por el usuario
                fts_audio_file = os.path.join(
                    settings.MEDIA_ROOT, audio_de_campana.audio_asterisk.name)

                if settings.FTS_ASTERISK_CONFIG_CHECK_AUDIO_FILE_EXISTS:
                    self._check_audio_file_exist(fts_audio_file, campana)

                params_audios = {
                    'fts_audio_de_campana_id': audio_de_campana.id,
                    'fts_audio_file': os.path.splitext(fts_audio_file)[0],
                }
                partes.append(TEMPLATE_DIALPLAN_PLAY_AUDIO.format(
                    **params_audios))

            elif audio_de_campana.archivo_de_audio:
                # Un audio de los pre-definidos / pre-cargados
                fts_audio_file = os.path.join(
                    settings.MEDIA_ROOT,
                    audio_de_campana.archivo_de_audio.audio_asterisk.name)

                if settings.FTS_ASTERISK_CONFIG_CHECK_AUDIO_FILE_EXISTS:
                    self._check_audio_file_exist(fts_audio_file, campana)

                params_audios = {
                    'fts_audio_de_campana_id': audio_de_campana.id,
                    'fts_audio_file': os.path.splitext(fts_audio_file)[0],
                }
                partes.append(TEMPLATE_DIALPLAN_PLAY_AUDIO.format(
                    **params_audios))

            elif audio_de_campana.tts:
                metadata = campana.bd_contacto.get_metadata()

                if metadata.dato_extra_es_hora(audio_de_campana.tts):
                    params_tts_hora = {
                        'fts_audio_de_campana_id': audio_de_campana.id,
                        'fts_tts_hora': audio_de_campana.tts,
                    }
                    partes.append(TEMPLATE_DIALPLAN_HORA.format(
                        **params_tts_hora))

                elif metadata.dato_extra_es_fecha(audio_de_campana.tts):
                    params_tts_fecha = {
                        'fts_audio_de_campana_id': audio_de_campana.id,
                        'fts_tts_fecha': audio_de_campana.tts,
                    }
                    partes.append(TEMPLATE_DIALPLAN_FECHA.format(
                        **params_tts_fecha))

                else:
                    # Es Teléfono, o es Genérico. En ambos casos se trata como
                    # tts genérico.
                    params_tts = {
                        'fts_audio_de_campana_id': audio_de_campana.id,
                        'fts_tts': audio_de_campana.tts,
                    }
                    partes.append(TEMPLATE_DIALPLAN_TTS.format(
                        **params_tts))

        partes.append(TEMPLATE_DIALPLAN_HANGUP.format(**param_generales))

        # TODO: derivacion: setear GrupoAtencion / QUEUE (cuando corresponda)
        # TODO: voicemail: IMPLEMENTAR!

        # Genera opciones de campana
        for opcion in campana.opciones.all():
            params_opcion = dict(param_generales)
            params_opcion.update({
                'fts_opcion_id': opcion.id,
                'fts_opcion_digito': opcion.digito,
            })

            if opcion.accion == Opcion.DERIVAR_GRUPO_ATENCION:
                ga = opcion.grupo_atencion
                params_opcion.update({
                    'fts_queue_name': ga.get_nombre_para_asterisk(),
                    'fts_grup_atencion_id': ga.id,
                })
                partes.append(TEMPLATE_OPCION_DERIVAR_GRUPO_ATENCION.format(
                              **params_opcion))

            elif opcion.accion == Opcion.DERIVAR_DERIVACION_EXTERNA:
                de = opcion.derivacion_externa
                params_opcion.update({
                    'fts_derivacion_externa_id': de.id,
                    'fts_dial_string': de.dial_string,
                })
                partes.append(
                    TEMPLATE_OPCION_DERIVAR_DERIVACION_EXTERNA.format(
                        **params_opcion))

            elif opcion.accion == Opcion.REPETIR:
                partes.append(TEMPLATE_OPCION_REPETIR.format(**params_opcion))

            elif opcion.accion == Opcion.VOICEMAIL:
                # TODO: implementar
                partes.append(TEMPLATE_OPCION_VOICEMAIL.format(
                              **params_opcion))

            elif opcion.accion == Opcion.CALIFICAR:
                params_opcion.update({
                    'fts_calificacion_id': opcion.calificacion.id,
                    'fts_calificacion_nombre': opcion.calificacion.nombre,
                })
                partes.append(TEMPLATE_OPCION_CALIFICAR.format(
                              **params_opcion))

            else:
                raise NoSePuedeCrearDialplanError(
                    "Tipo de acción '{0}' desconocida para la opcion."
                    "Campana '{1}'".format(opcion.accion, campana.id))

        partes.append(TEMPLATE_DIALPLAN_END.format(**param_generales))

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

                config_chunk = TEMPLATE_FAILED.format(
                    fts_campana_id=campana.id,
                    date=str(datetime.datetime.now()),
                    traceback_lines=traceback_lines
                )
            dialplan.append(config_chunk)

        self._dialplan_config_file.write(dialplan)


class QueueConfigCreator(object):
    def __init__(self):
        self._queue_config_file = QueueConfigFile()

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

        partes.append(TEMPLATE_QUEUE.format(**param_generales))

        for agente in grupo_atencion.agentes.all():
            params_opcion = dict(param_generales)
            params_opcion.update({
                'fts_member_number': agente.numero_interno,
                'fts_agente_id': agente.id
            })
            partes.append(TEMPLATE_QUEUE_MEMBER.format(**params_opcion))

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


class AsteriskConfigReloader(object):

    def reload_config(self):
        """Realiza reload de configuracion de Asterisk

        :returns: int -- exit status de proceso ejecutado.
                  0 (cero) si fue exitoso, otro valor si se produjo
                  un error
        """
        stdout_file = tempfile.TemporaryFile()
        stderr_file = tempfile.TemporaryFile()

        try:
            subprocess.check_call(settings.FTS_RELOAD_CMD,
                                  stdout=stdout_file, stderr=stderr_file)
            logger.info("Reload de configuracion de Asterisk fue OK")
            return 0
        except subprocess.CalledProcessError, e:
            logger.warn("Exit status erroneo: %s", e.returncode)
            logger.warn(" - Comando ejecutado: %s", e.cmd)
            try:
                stdout_file.seek(0)
                stderr_file.seek(0)
                stdout = stdout_file.read().splitlines()
                for line in stdout:
                    if line:
                        logger.warn(" STDOUT> %s", line)
                stderr = stderr_file.read().splitlines()
                for line in stderr:
                    if line:
                        logger.warn(" STDERR> %s", line)
            except:
                logger.exception("Error al intentar reporter STDERR y STDOUT")

            return e.returncode

        finally:
            stdout_file.close()
            stderr_file.close()


class ConfigFile(object):
    def __init__(self, filename):
        self._filename = filename

    def write(self, contenidos):
        tmp_fd, tmp_filename = tempfile.mkstemp()
        try:
            tmp_file_obj = os.fdopen(tmp_fd, 'w')
            for contenido in contenidos:
                tmp_file_obj.write(contenido)

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