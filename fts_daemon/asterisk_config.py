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
exten => _X.,n,Set(FtsDaemonCallId=${{CUT(EXTEN,,1)}})
exten => _X.,n,Set(NumberToCall=${{CUT(EXTEN,,2)}})
exten => _X.,n,NoOp(FTS,FtsDaemonCallId=${{FtsDaemonCallId}},NumberToCall=${{NumberToCall}})
exten => _X.,n,AGI(agi://{fts_agi_server}/{fts_campana_id}/${{FtsDaemonCallId}}/local-channel-pre-dial/)
exten => _X.,n,Dial({fts_dial_url},{fts_campana_dial_timeout})
; # TODO: *** WARN: el siguiente 'AGI()' a veces no es llamado
exten => _X.,n,AGI(agi://{fts_agi_server}/{fts_campana_id}/${{FtsDaemonCallId}}/local-channel-post-dial/dial-status/${{DIALSTATUS}}/)
exten => _X.,n,Hangup()

;----------------------------------------------------------------------
; Dialplan de campana (audio, opciones, etc)
;----------------------------------------------------------------------

[campania_{fts_campana_id}]

exten => _ftsX!,1,NoOp(FTS,INICIO,llamada=${{EXTEN:3}},campana={fts_campana_id})
exten => _ftsX!,n,Set(OriginalExten=${{EXTEN}})
exten => _ftsX!,n,Set(FtsDaemonCallId=${{EXTEN:3}})
exten => _ftsX!,n,AGI(agi://{fts_agi_server}/{fts_campana_id}/${{FtsDaemonCallId}}/inicio/)
exten => _ftsX!,n,Wait(1)
exten => _ftsX!,n,Answer()
exten => _ftsX!,n(audio),Background({fts_audio_file})
# FIXME: alcanza 'WaitExten(10)'??? No deberia ser un poco mas q' el tiempo del WAV/GSM/MP3?
exten => _ftsX!,n,WaitExten(10)
exten => _ftsX!,n,AGI(agi://{fts_agi_server}/{fts_campana_id}/${{FtsDaemonCallId}}/fin/)
exten => _ftsX!,n,Hangup()
"""


TEMPLATE_OPCION_REPETIR = """

; TEMPLATE_OPCION_REPETIR-{fts_opcion_id}
exten => {fts_opcion_digito},1,NoOp(FTS,REPETIR,llamada=${{FtsDaemonCallId}},campana={fts_campana_id})
exten => {fts_opcion_digito},n,AGI(agi://{fts_agi_server}/{fts_campana_id}/${{FtsDaemonCallId}}/opcion/{fts_opcion_digito}/{fts_opcion_id}/repetir/)
exten => {fts_opcion_digito},n,Goto(${{OriginalExten}},audio)
exten => {fts_opcion_digito},n,Hangup()

"""

TEMPLATE_OPCION_DERIVAR = """

; TEMPLATE_OPCION_DERIVAR-{fts_opcion_id}-{fts_grup_atencion_id}-{fts_queue_name}
exten => {fts_opcion_digito},1,NoOp(FTS,DERIVAR,llamada=${{FtsDaemonCallId}},campana={fts_campana_id},queue={fts_queue_name})
exten => {fts_opcion_digito},n,AGI(agi://{fts_agi_server}/{fts_campana_id}/${{FtsDaemonCallId}}/opcion/{fts_opcion_digito}/{fts_opcion_id}/derivar/)
exten => {fts_opcion_digito},n,Queue({fts_queue_name})
exten => {fts_opcion_digito},n,Hangup()

"""

TEMPLATE_OPCION_CALIFICAR = """

; TEMPLATE_OPCION_CALIFICAR-{fts_opcion_id}-{fts_calificacion_id}-{fts_calificacion_nombre}
exten => {fts_opcion_digito},1,NoOp(FTS,CALIFICAR,llamada=${{FtsDaemonCallId}},campana={fts_campana_id},calificacion={fts_calificacion_id}-fts_calificacion_nombre)
exten => {fts_opcion_digito},n,AGI(agi://{fts_agi_server}/{fts_campana_id}/${{FtsDaemonCallId}}/opcion/{fts_opcion_digito}/{fts_opcion_id}/calificar/{fts_calificacion_id}/)
exten => {fts_opcion_digito},n,Goto(${{OriginalExten}},audio)
exten => {fts_opcion_digito},n,Hangup()

"""

TEMPLATE_OPCION_VOICEMAIL = """

; TEMPLATE_OPCION_VOICEMAIL-{fts_opcion_id}
exten => {fts_opcion_digito},1,NoOp(FTS,VOICEMAIL,llamada=${{FtsDaemonCallId}},campana={fts_campana_id})
exten => {fts_opcion_digito},n,AGI(agi://{fts_agi_server}/{fts_campana_id}/${{FtsDaemonCallId}}/opcion/{fts_opcion_digito}/{fts_opcion_id}/voicemail/)
exten => {fts_opcion_digito},n,Goto(${{OriginalExten}},audio)
; TODO: IMPLEMENTAR!
exten => {fts_opcion_digito},n,Hangup()

"""

TEMPLATE_DIALPLAN_END = """

; TEMPLATE_DIALPLAN_END-{fts_campana_id}
exten => t,1,NoOp(FTS,ERR_T,llamada=${{FtsDaemonCallId}},campana={fts_campana_id})
exten => t,n,AGI(agi://{fts_agi_server}/{fts_campana_id}/${{FtsDaemonCallId}}/fin_err_t/)
exten => t,n,Hangup()

exten => i,1,NoOp(FTS,ERR_I,llamada=${{FtsDaemonCallId}},campana={fts_campana_id})
exten => i,n,AGI(agi://{fts_agi_server}/{fts_campana_id}/${{FtsDaemonCallId}}/fin_err_i/)
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


def generar_dialplan(campana):
    """Genera el dialplan para una campaña

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

    # audio_original -> lo chqeueamos por las dudas nomas...
    assert campana.audio_original is not None, "campana.audio_original == None"
    assert campana.audio_original.name,\
        "campana.audio_original.name no esta seteado"

    # audio_asterisk -> este tiene que existir si o si
    assert campana.audio_asterisk is not None, "campana.audio_asterisk == None"
    assert campana.audio_asterisk.name,\
        "campana.audio_asterisk.name no esta seteado"

    fts_audio_file = os.path.join(settings.MEDIA_ROOT,
        campana.audio_asterisk.name)
    if settings.FTS_ASTERISK_CONFIG_CHECK_AUDIO_FILE_EXISTS:
        if not os.path.exists(fts_audio_file):
            raise Exception("No se encontro el archivo de audio '%s' "
                "para la campana '%s'", fts_audio_file, campana.id)

    # Quitamos extension (Asterisk lo requiere asi)
    fts_audio_file = os.path.splitext(fts_audio_file)[0]

    partes = []
    param_generales = {
        'fts_campana_id': campana.id,
        'fts_campana_dial_timeout': campana.segundos_ring,
        'fts_audio_file': fts_audio_file,
        'fts_agi_server': 'localhost', # TODO: mover a settings
        'fts_dial_url': settings.ASTERISK['DIAL_URL'],
        'date': str(datetime.datetime.now())
    }

    partes.append(TEMPLATE_DIALPLAN_START.format(**param_generales))

    # TODO: derivacion: setear GrupoAtencion / QUEUE (cuando corresponda)
    # TODO: voicemail: IMPLEMENTAR!

    # Genera opciones de campana
    for opcion in campana.opciones.all():
        params_opcion = dict(param_generales)
        params_opcion.update({
            'fts_opcion_id': opcion.id,
            'fts_opcion_digito': opcion.digito,
        })

        if opcion.accion == Opcion.DERIVAR:
            ga = opcion.grupo_atencion
            params_opcion.update({
                'fts_queue_name': ga.get_nombre_para_asterisk(),
                'fts_grup_atencion_id': ga.id,
            })
            partes.append(TEMPLATE_OPCION_DERIVAR.format(**params_opcion))

        elif opcion.accion == Opcion.REPETIR:
            partes.append(TEMPLATE_OPCION_REPETIR.format(**params_opcion))

        elif opcion.accion == Opcion.VOICEMAIL:
            # TODO: implementar
            partes.append(TEMPLATE_OPCION_VOICEMAIL.format(**params_opcion))

        elif opcion.accion == Opcion.CALIFICAR:
            params_opcion.update({
                'fts_calificacion_id': opcion.calificacion.id,
                'fts_calificacion_nombre': opcion.calificacion.nombre,
            })
            partes.append(TEMPLATE_OPCION_CALIFICAR.format(**params_opcion))

        else:
            # FIXME: usar excepcion customizada
            raise Exception("Tipo de accion para opcion desconocida: {0}"
                "".format(opcion.accion))

    partes.append(TEMPLATE_DIALPLAN_END.format(**param_generales))

    return ''.join(partes)


def create_dialplan_config_file(campana=None, campanas=None):
    """Crea el archivo de dialplan para campanas existentes
    (si `campana` es None). Si `campana` es pasada por parametro,
    se genera solo para dicha campana.
    """

    if campanas:
        pass
    elif campana:
        campanas = [campana]
    else:
        campanas = Campana.objects.obtener_todas_para_generar_dialplan()

    tmp_fd, tmp_filename = tempfile.mkstemp()
    try:
        tmp_file_obj = os.fdopen(tmp_fd, 'w')
        for campana in campanas:
            logger.info("Creando dialplan para campana %s", campana.id)
            try:
                config_chunk = generar_dialplan(campana)
                logger.info("Dialplan generado OK para campana %s", campana.id)
            except:
                logger.exception("No se pudo generar configuracion de Asterisk"
                    " para la campana {0}".format(campana.id))

                try:
                    traceback_lines = ["; {0}".format(line)
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

            tmp_file_obj.write(config_chunk)

        tmp_file_obj.close()
        dest_filename = settings.FTS_DIALPLAN_FILENAME.strip()
        logger.info("Copiando dialplan a %s", dest_filename)
        shutil.copy(tmp_filename, dest_filename)

    finally:
        try:
            os.remove(tmp_filename)
        except:
            logger.exception("Error al intentar borrar temporal %s",
                tmp_filename)


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


def generar_queue(grupo_atencion):
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


def create_queue_config_file():
    """Crea el archivo de queue para G.A. existentes"""

    grupos_atencion = GrupoAtencion.objects.obtener_todos_para_generar_config()

    tmp_fd, tmp_filename = tempfile.mkstemp()
    try:
        tmp_file_obj = os.fdopen(tmp_fd, 'w')
        for ga in grupos_atencion:
            logger.info("Creando config para grupo de atencion %s", ga.id)
            config_chunk = generar_queue(ga)
            tmp_file_obj.write(config_chunk)

        tmp_file_obj.close()
        dest_filename = settings.FTS_QUEUE_FILENAME.strip()
        logger.info("Copiando config de queues a %s", dest_filename)
        shutil.copy(tmp_filename, dest_filename)

    finally:
        try:
            os.remove(tmp_filename)
        except:
            logger.exception("Error al intentar borrar temporal %s",
                tmp_filename)


def reload_config():
    """Realiza reload de configuracion de Asterisk

    Returns:
        - exit status de proceso ejecutado
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
