# -*- coding: utf-8 -*-

'''
Created on Apr 14, 2014

@author: Horacio G. de Oro
'''

from __future__ import unicode_literals

import os
import subprocess
import tempfile

from django.conf import settings
from django.core.files.storage import default_storage
from fts_web.errors import FtsAudioConversionError
from fts_web.models import Campana, upload_to_audios_asterisk
from fts_web.utiles import crear_archivo_en_media_root
import logging as _logging


logger = _logging.getLogger(__name__)


def convertir_audio_de_campana(campana):
    """Convierte archivo de audio de campaña,
    y actualiza la instancia de campaña

    Raises:
        FtsAudioConversionError: si se produjo algun tipo de error
    """
    assert isinstance(campana, Campana)

    wav_full_path = default_storage.path(campana.reproduccion.name)
    assert os.path.exists(wav_full_path)

    output_dir, outpu_filename = convertir_audio(wav_full_path,
        upload_to_audios_asterisk(campana, "-convertido-"))
    relative_filename = os.path.join(output_dir, outpu_filename)
    campana.audio_asterisk = relative_filename
    campana.save()


def convertir_audio(input_file_abs, output_filename_template):
    """Convierte archivo de audio de campaña.
    El archivo destino es creado en esta funcion.

    Parametros:
        input_file: path a archivo de entrada (.wav)

    Returns:
        - lo mismo que `crear_archivo_en_media_root()`: una tupla
            con 2 elementos:
                1) el directorio destino, relativo a MEDIA_ROOT
                2) el nombre del archivo

    Raises:
        FtsAudioConversionError: si se produjo algun tipo de error
    """

    # chequeos...
    if not os.path.exists(input_file_abs):
        logger.error("El archivo de entrada no existe: %s", input_file_abs)
        raise FtsAudioConversionError("El archivo de entrada no existe")

    if not os.path.abspath(input_file_abs):
        logger.error("El archivo de entrada no es un path absoluto: %s",
            input_file_abs)
        raise FtsAudioConversionError("El archivo de entrada no es "
            "un path absoluto")

    output_dir, outpu_filename = crear_archivo_en_media_root(
        output_filename_template)
    output_dir_abs = os.path.join(settings.MEDIA_ROOT, output_dir)
    output_file_abs = os.path.join(output_dir_abs, outpu_filename)
    # FIXME: borrar el temporal creado si se produce un error (asserts, etc.)

    assert os.path.isabs(output_dir_abs)
    assert os.path.isabs(output_file_abs)

    stdout_file = tempfile.TemporaryFile()
    stderr_file = tempfile.TemporaryFile()

    FTS_AUDIO_CONVERSOR = []
    for item in settings.TMPL_FTS_AUDIO_CONVERSOR:
        if item == "<INPUT_FILE>":
            FTS_AUDIO_CONVERSOR.append(input_file_abs)
        elif item == "<OUTPUT_FILE>":
            FTS_AUDIO_CONVERSOR.append(output_file_abs)
        else:
            FTS_AUDIO_CONVERSOR.append(item)

    assert input_file_abs in FTS_AUDIO_CONVERSOR
    assert output_file_abs in FTS_AUDIO_CONVERSOR

    # ejecutamos comando...
    try:
        logger.info("Iniciando conversion de audio de %s", input_file_abs)
        subprocess.check_call(FTS_AUDIO_CONVERSOR,
            stdout=stdout_file, stderr=stderr_file)
        logger.info("Conversion de audio finalizada exitosamente")
        return output_dir, outpu_filename

    except subprocess.CalledProcessError as e:
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
            logger.exception("Error al intentar reporter STDERR y STDOUT "
                "(lo ignoramos)")

        raise FtsAudioConversionError("Error detectado al ejecutar conversor",
            cause=e)

    finally:
        stdout_file.close()
        stderr_file.close()
