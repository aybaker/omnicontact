# -*- coding: utf-8 -*-

"""
Genera archivos de configuración para Asterisk: dialplan y queues.
"""

from __future__ import unicode_literals

import os
import pprint

from django.conf import settings
from fts_web.errors import FtsError
from fts_web.models import Campana, Opcion, AudioDeCampana
import logging as _logging


logger = _logging.getLogger(__name__)


class NoSePuedeCrearDialplanError(FtsError):
    """Indica que no se pudo crear el dialplan."""
    pass


class GeneradorDePedazo(object):
    """Generador de pedazo generico"""

    def get_template(self):
        raise(NotImplementedError())

    def get_parametros(self):
        raise(NotImplementedError())

    def _reportar_key_error(self):
        try:
            logger.exception("Clase: %s.\nTemplate:\n%s\n Params: %s",
                             str(self.__class__),
                             self.get_template(),
                             pprint.pformat(self.get_parametros()))
        except:
            pass

    def generar_pedazo(self):
        template = self.get_template()
        template = "\n".join(t.strip() for t in template.splitlines())
        try:
            return template.format(**self.get_parametros())
        except KeyError:
            self._reportar_key_error()
            raise

# ########################################################################### #
# Factory para el Dialplan.


def get_map():
    # FIXME: @@@@@ ACOMODAR ESTE METODO
    MAP_GENERADOR_PARA_START = {
        Campana.ACCION_NINGUNA:
            GeneradorParaStart,
        Campana.ACCION_DETECTAR_CONTESTADOR:
            GeneradorParaStartDetectarContestador,
        Campana.ACCION_DETECTAR_EVITAR_CONTESTADOR:
            GeneradorParaStartDetectarYEvitarContestador,
    }
    return MAP_GENERADOR_PARA_START


class GeneradorDePedazoDeDialplanFactory(object):

    def crear_generador_para_failed(self, parametros):
        return GeneradorParaFailed(parametros)

    def crear_generador_para_start(self, campana, parametros):
        try:
            class_de_generador = get_map()[campana.accion_contestador]
        except KeyError:
            raise(Exception("Tipo de accion para contestador desconocida: {0}"
                            .format(campana.accion_contestador)))

        generador = class_de_generador(parametros)
        return generador

    def crear_generador_para_audio(self, audio_de_campana, parametros,
                                   campana):

        if audio_de_campana.audio_asterisk:
            return GeneradorParaAudioAsterisk(audio_de_campana, parametros)

        elif audio_de_campana.archivo_de_audio:
            return GeneradorParaArchivoDeAudio(audio_de_campana, parametros)

        elif audio_de_campana.tts:
            metadata = campana.bd_contacto.get_metadata()

            if metadata.dato_extra_es_hora(audio_de_campana.tts):
                return GeneradorParaTtsHora(audio_de_campana, parametros)
            elif metadata.dato_extra_es_fecha(audio_de_campana.tts):
                return GeneradorParaTtsFecha(audio_de_campana, parametros)
            else:
                return self._crear_generador_para_tts(audio_de_campana,
                                                      parametros)
        else:
            raise(Exception("Tipo de audio de campana desconocido: {0}".format(
                audio_de_campana)))

    def _crear_generador_para_tts(self, audio_de_campana, parametros):
        if settings.FTS_TTS_UTILIZADO == settings.FTS_TTS_GOOGLE:
            return GeneradorParaTtsUsandoGoogle(audio_de_campana, parametros)
        elif settings.FTS_TTS_UTILIZADO == settings.FTS_TTS_SWIFT:
            return GeneradorParaTtsUsandoSwift(audio_de_campana, parametros)

    def crear_generador_para_hangup(self, parametros):
        return GeneradorParaHangup(parametros)

    def crear_generador_para_opcion(self, opcion, parametros, campana):
        assert isinstance(opcion, Opcion)

        if opcion.accion == Opcion.DERIVAR_GRUPO_ATENCION:
            return GeneradorParaOpcionGrupoAtencion(opcion, parametros)

        elif opcion.accion == Opcion.DERIVAR_DERIVACION_EXTERNA:
            return GeneradorParaOpcionDerivacionExterna(opcion, parametros)

        elif opcion.accion == Opcion.REPETIR:
            return GeneradorParaOpcionRepetir(opcion, parametros)

        elif opcion.accion == Opcion.VOICEMAIL:
            return GeneradorParaOpcionVoicemail(opcion, parametros)

        elif opcion.accion == Opcion.CALIFICAR:
            return GeneradorParaOpcionCalificar(opcion, parametros)

        else:
            raise NoSePuedeCrearDialplanError(
                "Tipo de acción '{0}' desconocida para la opcion."
                "Campana '{1}'".format(opcion.accion, campana.id))

    def crear_generador_para_end(self, parametros):
        return GeneradorParaEnd(parametros)


#==============================================================================
# Failed
#==============================================================================


class GeneradorDePedazoDeDialplanParaFailed(GeneradorDePedazo):
    """Interfaz / Clase abstracta para generar el pedazo de dialplan
    fallido para una campana.
    """

    def __init__(self, parametros):
        self._parametros = parametros


class GeneradorParaFailed(GeneradorDePedazoDeDialplanParaFailed):

    def get_template(self):
        return """

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

    def get_parametros(self):
        return self._parametros


#==============================================================================
# Start
#==============================================================================


class GeneradorDePedazoDeDialplanParaStart(GeneradorDePedazo):
    """Interfaz / Clase abstracta para generadores del pedazo inicial del
    dialplan para una campana.
    """

    def __init__(self, parametros):
        self._parametros = parametros


class GeneradorParaStart(GeneradorDePedazoDeDialplanParaStart):

    def get_template(self):
        return """

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

    def get_parametros(self):
        return self._parametros


class GeneradorParaStartDetectarContestador(
        GeneradorDePedazoDeDialplanParaStart):

    def get_template(self):
        return """

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

        ; http://www.voip-info.org/wiki/view/Asterisk+cmd+AMD
        ; AMDSTATUS -> MACHINE | HUMAN | NOTSURE | HANGUP
        exten => _ftsX.,n,AMD()
        exten => _ftsX.,n,GotoIf($["${{AMDSTATUS}}" == "MACHINE"]?amd_machine)
        exten => _ftsX.,n,GotoIf($["${{AMDSTATUS}}" == "HUMAN"]?amd_human)
        ; Por las dudas, lo tratamos como si fuera un humano
        exten => _ftsX.,n,AGI(agi://{fts_agi_server}/{fts_campana_id}/${{ContactoId}}/${{Intento}}/amd-detection-failed/)
        exten => _ftsX.,n,Goto(amd_finished)

        exten => _ftsX.,n(amd_machine),AGI(agi://{fts_agi_server}/{fts_campana_id}/${{ContactoId}}/${{Intento}}/amd-machine-detected/)
        exten => _ftsX.,n,Goto(amd_finished)

        exten => _ftsX.,n(amd_human),AGI(agi://{fts_agi_server}/{fts_campana_id}/${{ContactoId}}/${{Intento}}/amd-human-detected/)
        exten => _ftsX.,n,Goto(amd_finished)

        exten => _ftsX.,n(amd_finished),NoOp()
        exten => _ftsX.,n(audio),NoOp()

        """

    def get_parametros(self):
        return self._parametros


class GeneradorParaStartDetectarYEvitarContestador(
        GeneradorDePedazoDeDialplanParaStart):

    def get_template(self):
        return """

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

        ; http://www.voip-info.org/wiki/view/Asterisk+cmd+AMD
        ; AMDSTATUS -> MACHINE | HUMAN | NOTSURE | HANGUP
        exten => _ftsX.,n,AMD()
        exten => _ftsX.,n,GotoIf($["${{AMDSTATUS}}" == "MACHINE"]?amd_machine)
        exten => _ftsX.,n,GotoIf($["${{AMDSTATUS}}" == "HUMAN"]?amd_human)
        ; Por las dudas, lo tratamos como si fuera un humano
        exten => _ftsX.,n,AGI(agi://{fts_agi_server}/{fts_campana_id}/${{ContactoId}}/${{Intento}}/amd-detection-failed/)
        exten => _ftsX.,n,Goto(amd_finished)

        exten => _ftsX.,n(amd_machine),AGI(agi://{fts_agi_server}/{fts_campana_id}/${{ContactoId}}/${{Intento}}/amd-machine-detected/)
        exten => _ftsX.,n,Hangup()

        exten => _ftsX.,n(amd_human),AGI(agi://{fts_agi_server}/{fts_campana_id}/${{ContactoId}}/${{Intento}}/amd-human-detected/)
        exten => _ftsX.,n,Goto(amd_finished)

        exten => _ftsX.,n(amd_finished),NoOp()
        exten => _ftsX.,n(audio),NoOp()

        """

    def get_parametros(self):
        return self._parametros


#==============================================================================
# Audios
#==============================================================================

class GeneradorDePedazoDeDialplanParaAudio(GeneradorDePedazo):
    """Interfaz / Clase abstracta para generadores de pedazos de dialplan
    relacionados con los AUDIOS de una campana
    """

    def __init__(self, audio_de_campana, parametros):
        assert isinstance(audio_de_campana, AudioDeCampana)
        self._audio_de_campana = audio_de_campana
        self._parametros = parametros

    def _check_audio_file_exist(self, fts_audio_file, campana):
        if not os.path.exists(fts_audio_file):
            raise NoSePuedeCrearDialplanError(
                "No se encontro el archivo de audio '{0}' para la campana "
                "'{1}'".format(fts_audio_file, campana.id))


class GeneradorParaAudioAsterisk(GeneradorDePedazoDeDialplanParaAudio):

    def get_template(self):
        return """

        ; TEMPLATE_DIALPLAN_PLAY_AUDIO-{fts_audio_de_campana_id}
        exten => _ftsX.,n,Background({fts_audio_file})

        """

    def get_parametros(self):

        # Un archivo subido por el usuario
        fts_audio_file = os.path.join(
            settings.MEDIA_ROOT, self._audio_de_campana.audio_asterisk.name)

        if settings.FTS_ASTERISK_CONFIG_CHECK_AUDIO_FILE_EXISTS:
            self._check_audio_file_exist(fts_audio_file,
                                         self._audio_de_campana.campana)

        parametros = dict(self._parametros)
        parametros.update({
            'fts_audio_de_campana_id': self._audio_de_campana.id,
            'fts_audio_file': os.path.splitext(fts_audio_file)[0],
        })

        return parametros


class GeneradorParaArchivoDeAudio(GeneradorDePedazoDeDialplanParaAudio):

    def get_template(self):
        return """

        ; TEMPLATE_DIALPLAN_PLAY_AUDIO-{fts_audio_de_campana_id}
        exten => _ftsX.,n,Background({fts_audio_file})

        """

    def get_parametros(self):

        fts_audio_file = os.path.join(
            settings.MEDIA_ROOT,
            self._audio_de_campana.archivo_de_audio.audio_asterisk.name)

        if settings.FTS_ASTERISK_CONFIG_CHECK_AUDIO_FILE_EXISTS:
            self._check_audio_file_exist(fts_audio_file,
                                         self._audio_de_campana.campana)

        parametros = dict(self._parametros)
        parametros.update({
            'fts_audio_de_campana_id': self._audio_de_campana.id,
            'fts_audio_file': os.path.splitext(fts_audio_file)[0],
        })

        return parametros


class GeneradorParaTtsHora(GeneradorDePedazoDeDialplanParaAudio):

    def get_template(self):
        return """

        ; TEMPLATE_DIALPLAN_HORA-{fts_audio_de_campana_id}
        exten => _ftsX.,n,NoOp(TTS,{fts_tts_hora}_hora,${{{fts_tts_hora}_hora}})
        exten => _ftsX.,n,Saynumber(${{{fts_tts_hora}_hora}})
        exten => _ftsX.,n,Playback(horas)
        exten => _ftsX.,n,NoOp(TTS,{fts_tts_hora}_min,${{{fts_tts_hora}_min}})
        exten => _ftsX.,n,Saynumber(${{{fts_tts_hora}_min}})
        exten => _ftsX.,n,Playback(minutos)

        """

    def get_parametros(self):
        params_tts_hora = {
            'fts_audio_de_campana_id': self._audio_de_campana.id,
            'fts_tts_hora': self._audio_de_campana.tts,
        }
        return params_tts_hora


class GeneradorParaTtsFecha(GeneradorDePedazoDeDialplanParaAudio):

    def get_template(self):
        return """

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

    def get_parametros(self):
        params_tts_fecha = {
            'fts_audio_de_campana_id': self._audio_de_campana.id,
            'fts_tts_fecha': self._audio_de_campana.tts,
        }
        return params_tts_fecha


class GeneradorParaTtsUsandoGoogle(GeneradorDePedazoDeDialplanParaAudio):

    def get_template(self):
        return """

        ; TEMPLATE_DIALPLAN_TTS-{fts_audio_de_campana_id}
        exten => _ftsX.,n,NoOp(TTS,{fts_tts},${{{fts_tts}}})
        exten => _ftsX.,n,AGI(googletts.agi,${{{fts_tts}}},es)

        """

    def get_parametros(self):
        params_tts = {
            'fts_audio_de_campana_id': self._audio_de_campana.id,
            'fts_tts': self._audio_de_campana.tts,
        }
        return params_tts


class GeneradorParaTtsUsandoSwift(GeneradorDePedazoDeDialplanParaAudio):

    def get_template(self):
        # TODO: Revisar que este bien implementado el template con Swift.
        return """

        ; TEMPLATE_DIALPLAN_TTS-{fts_audio_de_campana_id}
        exten => _ftsX.,n,NoOp(TTS,{fts_tts},${{{fts_tts}}})
        exten => _ftsX.,n,Swift(${{{fts_tts}}})

        """

    def get_parametros(self):
        params_tts = {
            'fts_audio_de_campana_id': self._audio_de_campana.id,
            'fts_tts': self._audio_de_campana.tts,
        }
        return params_tts


#==============================================================================
# Hangup
#==============================================================================


class GeneradorDePedazoDeDialplanParaHangup(GeneradorDePedazo):
    """Interfaz / Clase abstracta para generadores del pedazo de hangup del
    dialplan para una campana.
    """

    def __init__(self, parametros):
        self._parametros = parametros


class GeneradorParaHangup(GeneradorDePedazoDeDialplanParaHangup):

    def get_template(self):
        return """

        ; TEMPLATE_DIALPLAN_HANGUP-{fts_campana_id}
        ; TODO: alcanza 'WaitExten(10)'?
        exten => _ftsX.,n,WaitExten(10)
        exten => _ftsX.,n,AGI(agi://{fts_agi_server}/{fts_campana_id}/${{ContactoId}}/${{Intento}}/fin/)
        exten => _ftsX.,n,Hangup()

        """

    def get_parametros(self):
        return self._parametros


#==============================================================================
# Opciones
#==============================================================================

class GeneradorDePedazoDeDialplanParaOpcion(GeneradorDePedazo):
    """Interfaz / Clase abstracta para generadores de pedazos de dialplan
    relacionados con las Opciones de una campana
    """

    def __init__(self, opcion, parametros):
        assert isinstance(opcion, Opcion)
        self._opcion = opcion
        self._parametros = parametros


class GeneradorParaOpcionVoicemail(GeneradorDePedazoDeDialplanParaOpcion):

    def get_template(self):
        return """

        ; TEMPLATE_OPCION_VOICEMAIL-{fts_opcion_id}
        exten => {fts_opcion_digito},1,NoOp(FTS,VOICEMAIL,llamada=${{ContactoId}},campana={fts_campana_id})
        exten => {fts_opcion_digito},n,AGI(agi://{fts_agi_server}/{fts_campana_id}/${{ContactoId}}/${{Intento}}/opcion/{fts_opcion_digito}/{fts_opcion_id}/voicemail/)
        exten => {fts_opcion_digito},n,Goto(${{OriginalExten}},audio)
        ; TODO: IMPLEMENTAR!
        exten => {fts_opcion_digito},n,Hangup()

        """

    def get_parametros(self):
        return self._parametros


class GeneradorParaOpcionCalificar(GeneradorDePedazoDeDialplanParaOpcion):

    def get_template(self):
        return """

        ; TEMPLATE_OPCION_CALIFICAR-{fts_opcion_id}-{fts_calificacion_id}-{fts_calificacion_nombre}
        exten => {fts_opcion_digito},1,NoOp(FTS,CALIFICAR,llamada=${{ContactoId}},campana={fts_campana_id},calificacion={fts_calificacion_id}-fts_calificacion_nombre)
        exten => {fts_opcion_digito},n,AGI(agi://{fts_agi_server}/{fts_campana_id}/${{ContactoId}}/${{Intento}}/opcion/{fts_opcion_digito}/{fts_opcion_id}/calificar/{fts_calificacion_id}/)
        exten => {fts_opcion_digito},n,Playback(demo-thanks)
        exten => {fts_opcion_digito},n,Hangup()

        """

    def get_parametros(self):
        parametros = dict(self._parametros)
        parametros.update({
            'fts_calificacion_id': self._opcion.calificacion.id,
            'fts_calificacion_nombre': self._opcion.calificacion.nombre,
        })
        return parametros


class GeneradorParaOpcionGrupoAtencion(GeneradorDePedazoDeDialplanParaOpcion):

    def get_template(self):
        return """

        ; TEMPLATE_OPCION_DERIVAR_GRUPO_ATENCION-{fts_opcion_id}-{fts_grup_atencion_id}-{fts_queue_name}
        exten => {fts_opcion_digito},1,NoOp(FTS,DERIVAR_GRUPO_ATENCION,llamada=${{ContactoId}},campana={fts_campana_id},queue={fts_queue_name})
        exten => {fts_opcion_digito},n,AGI(agi://{fts_agi_server}/{fts_campana_id}/${{ContactoId}}/${{Intento}}/opcion/{fts_opcion_digito}/{fts_opcion_id}/derivar/)
        exten => {fts_opcion_digito},n,Queue({fts_queue_name})
        exten => {fts_opcion_digito},n,Hangup()

        """

    def get_parametros(self):
        parametros = dict(self._parametros)
        ga = self._opcion.grupo_atencion
        parametros.update({
            'fts_queue_name': ga.get_nombre_para_asterisk(),
            'fts_grup_atencion_id': ga.id,
        })
        return parametros


class GeneradorParaOpcionDerivacionExterna(
    GeneradorDePedazoDeDialplanParaOpcion):

    def get_template(self):
        return """

        ; TEMPLATE_OPCION_DERIVAR_DERIVACION_EXTERNA-{fts_opcion_id}-{fts_derivacion_externa_id}-{fts_dial_string}
        exten => {fts_opcion_digito},1,NoOp(FTS,DERIVAR_DERIVACION_EXTERNA,llamada=${{ContactoId}},campana={fts_campana_id},dial_string={fts_dial_string})
        exten => {fts_opcion_digito},n,AGI(agi://{fts_agi_server}/{fts_campana_id}/${{ContactoId}}/${{Intento}}/opcion/{fts_opcion_digito}/{fts_opcion_id}/derivacion_externa/)
        exten => {fts_opcion_digito},n,SIPAddHeader(DNI:${{DNI}})
        exten => {fts_opcion_digito},n,Dial({fts_dial_string})
        exten => {fts_opcion_digito},n,Hangup()

        """

    def get_parametros(self):
        parametros = dict(self._parametros)
        de = self._opcion.derivacion_externa
        parametros.update({
            'fts_derivacion_externa_id': de.id,
            'fts_dial_string': de.dial_string,
        })
        return parametros


class GeneradorParaOpcionRepetir(GeneradorDePedazoDeDialplanParaOpcion):

    def get_template(self):
        return """

        ; TEMPLATE_OPCION_REPETIR-{fts_opcion_id}
        exten => {fts_opcion_digito},1,NoOp(FTS,REPETIR,llamada=${{ContactoId}},campana={fts_campana_id})
        exten => {fts_opcion_digito},n,AGI(agi://{fts_agi_server}/{fts_campana_id}/${{ContactoId}}/${{Intento}}/opcion/{fts_opcion_digito}/{fts_opcion_id}/repetir/)
        exten => {fts_opcion_digito},n,Goto(${{OriginalExten}},audio)
        exten => {fts_opcion_digito},n,Hangup()

        """

    def get_parametros(self):
        return self._parametros


#==============================================================================
# End
#==============================================================================


class GeneradorDePedazoDeDialplanParaEnd(GeneradorDePedazo):
    """Interfaz / Clase abstracta para generadores del pedazo final del
    dialplan para una campana.
    """

    def __init__(self, parametros):
        self._parametros = parametros


class GeneradorParaEnd(GeneradorDePedazoDeDialplanParaEnd):

    def get_template(self):
        return """

        ; TEMPLATE_DIALPLAN_END-{fts_campana_id}
        exten => t,1,NoOp(FTS,ERR_T,llamada=${{ContactoId}},campana={fts_campana_id})
        exten => t,n,AGI(agi://{fts_agi_server}/{fts_campana_id}/${{ContactoId}}/${{Intento}}/fin_err_t/)
        exten => t,n,Hangup()

        exten => i,1,NoOp(FTS,ERR_I,llamada=${{ContactoId}},campana={fts_campana_id})
        exten => i,n,AGI(agi://{fts_agi_server}/{fts_campana_id}/${{ContactoId}}/${{Intento}}/fin_err_i/)
        exten => i,n,Hangup()

        """

    def get_parametros(self):
        return self._parametros


# ########################################################################### #
# Factory para las Queue.

class GeneradorDePedazoDeQueueFactory(object):

    def crear_generador_para_queue(self, parametros):
        return GeneradorParaQueue(parametros)

    def crear_generador_para_member(self, agente, parametros):
        return GeneradorParaMember(agente, parametros)

#==============================================================================
# Queue
#==============================================================================


class GeneradorDePedazoDeQueue(GeneradorDePedazo):
    """Interfaz / Clase abstracta para generar el pedazo de queue para una
    campana.
    """

    def __init__(self, parametros):
        self._parametros = parametros


class GeneradorParaQueue(GeneradorDePedazoDeQueue):

    def get_template(self):
        return """
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

    def get_parametros(self):
        return self._parametros


#==============================================================================
# Member
#==============================================================================


class GeneradorDePedazoDeMember(GeneradorDePedazo):
    """Interfaz / Clase abstracta para generar el pedazo de queue Member
    para una campana.
    """

    def __init__(self, agente, parametros):
        self._agente = agente
        self._parametros = parametros


class GeneradorParaMember(GeneradorDePedazoDeMember):

    def get_template(self):
        return """

        ; agente.id={fts_agente_id}
        member => SIP/{fts_member_number}

        """

    def get_parametros(self):
        params_member = dict(self._parametros)
        params_member.update({
            'fts_member_number': self._agente.numero_interno,
            'fts_agente_id': self._agente.id
        })
        return params_member
