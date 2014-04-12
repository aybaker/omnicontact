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

exten => _XXXXXX!.,1,Answer()
 same => _XXXXXX!.,n,Wait(1)
 same => _XXXXXX!.,n,AGI(agi://{fts_agi_server}/{fts_campana_id}/${{FtsDaemonCallId}}/inicio/)
 same => _XXXXXX!.,n(audio),Background({fts_audio_file})
 same => _XXXXXX!.,n,WaitExten(5)
 same => _XXXXXX!.,n,Hangup()

"""


TEMPLATE_OPCION_REPETIR = """

; TEMPLATE_OPCION_REPETIR-{fts_opcion_id}
exten => {fts_opcion_digito},1,AGI(agi://{fts_agi_server}/{fts_campana_id}/${{FtsDaemonCallId}}/opcion/{fts_opcion_id}/)
exten => {fts_opcion_digito},n,Goto(${{id_num}},audio)
exten => {fts_opcion_digito},n,Hangup()

"""

TEMPLATE_OPCION_DERIVAR = """

; TEMPLATE_OPCION_DERIVAR-{fts_opcion_id}
exten => {fts_opcion_digito},1,AGI(agi://{fts_agi_server}/{fts_campana_id}/${{FtsDaemonCallId}}/opcion/{fts_opcion_id}/)
exten => {fts_opcion_digito},n,Queue({fts_queue_name})
exten => {fts_opcion_digito},n,Hangup()

"""


TEMPLATE_DIALPLAN_END = """

; TEMPLATE_DIALPLAN_END-{fts_campana_id}
exten => t,1,AGI(agi://{fts_agi_server}/{fts_campana_id}/${{FtsDaemonCallId}}/fin_err/t/)
exten => t,n,Hangup()
exten => i,1,AGI(agi://{fts_agi_server}/{fts_campana_id}/${{FtsDaemonCallId}}/fin_err/i/)
exten => i,n,Hangup()

"""


def generar_dialplan(campana):
    """Genera el dialplan para una campaña"""
    partes = []
    params = {
        'fts_campana_id': campana.id,
        'fts_audio_file': '/tmp/sample.wav',
        'fts_agi_server': 'localhost', # TODO: mover a settings
        'date': str(datetime.datetime.now())
    }
    partes.append(TEMPLATE_DIALPLAN_START.format(**params))
    
    # Genera opciones de campana
    for opcion in campana.opciones.all():
        params_opcion = dict(params)
        params_opcion.update({
            'fts_opcion_id': opcion.id,
            'fts_opcion_digito': opcion.digito,
        })
        if opcion.accion == Opcion.DERIVAR:
            partes.append(TEMPLATE_OPCION_DERIVAR.format(**params_opcion))
        elif opcion.accion == Opcion.REPETIR:
            partes.append(TEMPLATE_OPCION_REPETIR.format(**params_opcion))
        else:
            raise Exception("Tipo de accion para opcion desconocida: {0}"
                "".format(opcion.accion))

    partes.append(TEMPLATE_DIALPLAN_END.format(**params))
    
    return ''.join(partes)
