# -*- coding: utf-8 -*-

'''
Created on Apr 11, 2014

@author: Horacio G. de Oro
'''


from __future__ import unicode_literals

import datetime


TEMPLATE_DIALPLAN_START = """

;----------------------------------------------------------------------
; TEMPLATE_DIALPLAN_START-{fts_campana_id}
;   Autogenerado {date}
;----------------------------------------------------------------------

[campania_{fts_campana_id}]

exten => _XXXXXX!.,1,Answer()
 same => _XXXXXX!.,n,Wait(1)
 same => _XXXXXX!.,n,Agi(ivr_incompleta.php,${{id_num}},${{campania}})
 same => _XXXXXX!.,n(audio),Background({fts_audio_file})
 same => _XXXXXX!.,n,WaitExten(5)
 same => _XXXXXX!.,n,Hangup()

; exten => 1,1,Agi(ivr_completada.php,${{id_num}},{fts_campana_id})
; exten => 1,n,Hangup()
;
; exten => 2,1,Agi(ivr_completada.php,${{id_num}},{fts_campana_id})
; exten => 2,n,Hangup()
;
; exten => 3,1,Queue(queue1)
; exten => 3,n,Hangup()
;
; exten => 0,1,Goto(${{id_num}},audio)
; exten => 0,n,Hangup()

"""


TEMPLATE_OPCION = """

:
; TEMPLATE_OPCION-{fts_opcion_id}
;

exten => 1,1,Agi(ivr_opcion_seleccionada.php,{fts_opcion_id},{fts_campana_id})
exten => 1,n,Hangup()

"""


TEMPLATE_DIALPLAN_END = """

:
; TEMPLATE_DIALPLAN_END-{fts_campana_id}
;

exten => t,1,Hangup()
exten => i,1,Hangup()

"""


def generar_dialplan(campana):
    """Genera el dialplan para una campaña"""
    partes = []
    params = {
        'fts_campana_id': campana.id,
        'fts_audio_file': '/tmp/sample.wav',
        'date': str(datetime.datetime.now())
    }
    partes.append(TEMPLATE_DIALPLAN_START.format(**params))
    
    # Genera opciones de campana
    for opcion in campana.opciones.all():
        partes.append(TEMPLATE_OPCION.format(fts_opcion_id=opcion.id,
            **params))

    partes.append(TEMPLATE_DIALPLAN_END.format(**params))
    
    return ''.join(partes)
