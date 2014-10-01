# -*- coding: utf-8 -*-

"""
Genera archivos de configuración para Asterisk: dialplan y queues.
"""

from __future__ import unicode_literals

import os

from django.conf import settings
from fts_web.errors import FtsError
from fts_web.models import Opcion, Campana, GrupoAtencion, AudioDeCampana
import logging as _logging
import pprint


logger = _logging.getLogger(__name__)


class NoSePuedeCrearDialplanError(FtsError):
    """Indica que no se pudo crear el dialplan."""
    pass


class GeneradorDePedazoDeDialplanFactory(object):

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

    def crear_generador_para_audio(self,
                                   audio_de_campana,
                                   parametros,
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
                return GeneradorParaTts(audio_de_campana, parametros)

        else:
            raise(Exception("Tipo de audio de campana desconocido: {0}".format(
                audio_de_campana)))


#==============================================================================
# Opciones
#==============================================================================

class GeneradorDePedazoDeDialplanParaOpcion(object):
    """Interfaz / Clase abstracta para generadores de dialplan"""

    def __init__(self, opcion, parametros):
        assert isinstance(opcion, Opcion)
        self._opcion = opcion
        self._parametros = parametros

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
        try:
            return self.get_template().format(**self.get_parametros())
        except KeyError:
            self._reportar_key_error()
            raise


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
# Audios
#==============================================================================

class GeneradorDePedazoDeDialplanParaAudio(object):
    """Interfaz / Clase abstracta para generadores de dialplan"""

    def __init__(self, audio_de_campana, parametros):
        assert isinstance(audio_de_campana, AudioDeCampana)
        self._audio_de_campana = audio_de_campana
        self._parametros = parametros

    def get_template(self):
        raise(NotImplementedError())

    def get_parametros(self):
        raise(NotImplementedError())

    def generar_pedazo(self):
        return self.get_template().format(**self.get_parametros())


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


class GeneradorParaTts(GeneradorDePedazoDeDialplanParaAudio):

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
