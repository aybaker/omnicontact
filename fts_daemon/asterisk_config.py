# -*- coding: utf-8 -*-

'''
Created on Apr 11, 2014

@author: Horacio G. de Oro
'''


from __future__ import unicode_literals

import datetime
from fts_web.models import Opcion


TEMPLATE_DIALPLAN_START = """

;----------------------------------------------------------------------
; TEMPLATE_DIALPLAN_START-{fts_campana_id}
;   Autogenerado {date}
;----------------------------------------------------------------------

[campania_{fts_campana_id}]

exten => _XXXXXX!.,1,NoOp(FTS,INICIO,llamada=${{FtsDaemonCallId}},campana={fts_campana_id})
 same => _XXXXXX!.,n,AGI(agi://{fts_agi_server}/{fts_campana_id}/${{FtsDaemonCallId}}/inicio/)
 same => _XXXXXX!.,n,Wait(1)
 same => _XXXXXX!.,n,Answer()
 same => _XXXXXX!.,n(audio),Background({fts_audio_file})
 same => _XXXXXX!.,n,WaitExten(5)
 same => _XXXXXX!.,n,Hangup()

"""


TEMPLATE_OPCION_REPETIR = """

; TEMPLATE_OPCION_REPETIR-{fts_opcion_id}
exten => {fts_opcion_digito},1,NoOp(FTS,REPETIR,llamada=${{FtsDaemonCallId}},campana={fts_campana_id})
exten => {fts_opcion_digito},n,AGI(agi://{fts_agi_server}/{fts_campana_id}/${{FtsDaemonCallId}}/opcion/{fts_opcion_id}/repetir/)
exten => {fts_opcion_digito},n,Goto(audio)
exten => {fts_opcion_digito},n,Hangup()

"""

TEMPLATE_OPCION_DERIVAR = """

; TEMPLATE_OPCION_DERIVAR-{fts_opcion_id}
exten => {fts_opcion_digito},1,NoOp(FTS,DERIVAR,llamada=${{FtsDaemonCallId}},campana={fts_campana_id},queue={fts_queue_name})
exten => {fts_opcion_digito},n,AGI(agi://{fts_agi_server}/{fts_campana_id}/${{FtsDaemonCallId}}/opcion/{fts_opcion_id}/derivar/)
exten => {fts_opcion_digito},n,Queue({fts_queue_name})
exten => {fts_opcion_digito},n,Hangup()

"""

TEMPLATE_OPCION_CALIFICAR = """

; TEMPLATE_OPCION_CALIFICAR-{fts_opcion_id}
exten => {fts_opcion_digito},1,NoOp(FTS,CALIFICAR,llamada=${{FtsDaemonCallId}},campana={fts_campana_id})
exten => {fts_opcion_digito},n,AGI(agi://{fts_agi_server}/{fts_campana_id}/${{FtsDaemonCallId}}/opcion/{fts_opcion_id}/calificar/)
exten => {fts_opcion_digito},n,Goto(audio)
; TODO: IMPLEMENTAR!
exten => {fts_opcion_digito},n,Hangup()

"""

TEMPLATE_OPCION_VOICEMAIL = """

; TEMPLATE_OPCION_VOICEMAIL-{fts_opcion_id}
exten => {fts_opcion_digito},1,NoOp(FTS,VOICEMAIL,llamada=${{FtsDaemonCallId}},campana={fts_campana_id})
exten => {fts_opcion_digito},n,AGI(agi://{fts_agi_server}/{fts_campana_id}/${{FtsDaemonCallId}}/opcion/{fts_opcion_id}/voicemail/)
exten => {fts_opcion_digito},n,Goto(audio)
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
    # TODO: calificacion: IMPLEMENTAR!

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
            })
            partes.append(TEMPLATE_OPCION_DERIVAR.format(**params_opcion))

        elif opcion.accion == Opcion.REPETIR:
            partes.append(TEMPLATE_OPCION_REPETIR.format(**params_opcion))

        elif opcion.accion == Opcion.VOICEMAIL:
            partes.append(TEMPLATE_OPCION_VOICEMAIL.format(**params_opcion))

        elif opcion.accion == Opcion.CALIFICAR:
            partes.append(TEMPLATE_OPCION_CALIFICAR.format(**params_opcion))

        else:
            raise Exception("Tipo de accion para opcion desconocida: {0}"
                "".format(opcion.accion))

    partes.append(TEMPLATE_DIALPLAN_END.format(**param_generales))
    
    return ''.join(partes)
