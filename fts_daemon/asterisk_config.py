# -*- coding: utf-8 -*-

'''
Created on Apr 11, 2014

@author: Horacio G. de Oro
'''


from __future__ import unicode_literals

import datetime

from django.conf import settings
from fts_web.models import Opcion, Campana, GrupoAtencion
import os
import logging as _logging
import tempfile
import shutil
import subprocess


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

[campania_{fts_campana_id}]

exten => _ftsX!,1,NoOp(FTS,INICIO,llamada=${{EXTEN:3}},campana={fts_campana_id})
exten => _ftsX!,n,Set(OriginalExten=${{EXTEN}})
exten => _ftsX!,n,Set(FtsDaemonCallId=${{EXTEN:3}})
exten => _ftsX!,n,AGI(agi://{fts_agi_server}/{fts_campana_id}/${{FtsDaemonCallId}}/inicio/)
exten => _ftsX!,n,Wait(1)
exten => _ftsX!,n,Answer()
exten => _ftsX!,n(audio),Background({fts_audio_file})
exten => _ftsX!,n,WaitExten(10)
exten => _ftsX!,n,Hangup()

"""


TEMPLATE_OPCION_REPETIR = """

; TEMPLATE_OPCION_REPETIR-{fts_opcion_id}
exten => {fts_opcion_digito},1,NoOp(FTS,REPETIR,llamada=${{FtsDaemonCallId}},campana={fts_campana_id})
exten => {fts_opcion_digito},n,AGI(agi://{fts_agi_server}/{fts_campana_id}/${{FtsDaemonCallId}}/opcion/{fts_opcion_id}/repetir/)
exten => {fts_opcion_digito},n,Goto(${{OriginalExten}},audio)
exten => {fts_opcion_digito},n,Hangup()

"""

TEMPLATE_OPCION_DERIVAR = """

; TEMPLATE_OPCION_DERIVAR-{fts_opcion_id}-{fts_grup_atencion_id}-{fts_queue_name}
exten => {fts_opcion_digito},1,NoOp(FTS,DERIVAR,llamada=${{FtsDaemonCallId}},campana={fts_campana_id},queue={fts_queue_name})
exten => {fts_opcion_digito},n,AGI(agi://{fts_agi_server}/{fts_campana_id}/${{FtsDaemonCallId}}/opcion/{fts_opcion_id}/derivar/)
exten => {fts_opcion_digito},n,Queue({fts_queue_name})
exten => {fts_opcion_digito},n,Hangup()

"""

TEMPLATE_OPCION_CALIFICAR = """

; TEMPLATE_OPCION_CALIFICAR-{fts_opcion_id}-{fts_calificacion_id}-{fts_calificacion_nombre}
exten => {fts_opcion_digito},1,NoOp(FTS,CALIFICAR,llamada=${{FtsDaemonCallId}},campana={fts_campana_id},calificacion={fts_calificacion_id}-fts_calificacion_nombre)
exten => {fts_opcion_digito},n,AGI(agi://{fts_agi_server}/{fts_campana_id}/${{FtsDaemonCallId}}/opcion/{fts_opcion_id}/calificar/{fts_calificacion_id}/)
exten => {fts_opcion_digito},n,Goto(${{OriginalExten}},audio)
exten => {fts_opcion_digito},n,Hangup()

"""

TEMPLATE_OPCION_VOICEMAIL = """

; TEMPLATE_OPCION_VOICEMAIL-{fts_opcion_id}
exten => {fts_opcion_digito},1,NoOp(FTS,VOICEMAIL,llamada=${{FtsDaemonCallId}},campana={fts_campana_id})
exten => {fts_opcion_digito},n,AGI(agi://{fts_agi_server}/{fts_campana_id}/${{FtsDaemonCallId}}/opcion/{fts_opcion_id}/voicemail/)
exten => {fts_opcion_digito},n,Goto(${{OriginalExten}},audio)
; TODO: IMPLEMENTAR!
exten => {fts_opcion_digito},n,Hangup()

"""

TEMPLATE_DIALPLAN_END = """

; TEMPLATE_DIALPLAN_END-{fts_campana_id}
exten => t,1,NoOp(FTS,ERR_T,llamada=${{FtsDaemonCallId}},campana={fts_campana_id})
exten => t,n,AGI(agi://{fts_agi_server}/{fts_campana_id}/${{FtsDaemonCallId}}/fin_err/t/)
exten => t,n,Hangup()

exten => i,1,NoOp(FTS,ERR_I,llamada=${{FtsDaemonCallId}},campana={fts_campana_id})
exten => i,n,AGI(agi://{fts_agi_server}/{fts_campana_id}/${{FtsDaemonCallId}}/fin_err/i/)
exten => i,n,Hangup()

"""


def generar_dialplan(campana):
    """Genera el dialplan para una campaña"""

    partes = []
    param_generales = {
        'fts_campana_id': campana.id,
        'fts_audio_file': '/tmp/sample.wav',
        'fts_agi_server': 'localhost', # TODO: mover a settings
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
            raise Exception("Tipo de accion para opcion desconocida: {0}"
                "".format(opcion.accion))

    partes.append(TEMPLATE_DIALPLAN_END.format(**param_generales))
    
    return ''.join(partes)


def create_dialplan_config_file(campana=None):
    """Crea el archivo de dialplan para campanas existentes
    (si `campana` es None). Si `campana` es pasada por parametro,
    se genera solo para dicha campana.
    """

    if campana is None:
        campanas = Campana.objects.obtener_todas_para_generar_dialplan()
    else:
        campanas = [campana]

    tmp_fd, tmp_filename = tempfile.mkstemp()
    try:
        tmp_file_obj = os.fdopen(tmp_fd, 'w')
        for campana in campanas:
            logger.info("Creando dialplan para campana %s", campana.id)
            config_chunk = generar_dialplan(campana)
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
