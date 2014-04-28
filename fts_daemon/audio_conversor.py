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
from fts_web.models import Campana
from fts_web.utiles import crear_archivo_en_media_root
import logging as _logging
import uuid


logger = _logging.getLogger(__name__)


def convertir_audio_de_campana(campana):
    """Convierte archivo de audio de campaña,
    y actualiza la instancia de campaña

    Raises:
        FtsAudioConversionError: si se produjo algun tipo de error
    """
    assert isinstance(campana, Campana)

    # chequea archivo original (a convertir)
    wav_full_path = default_storage.path(campana.reproduccion.name)
    assert os.path.exists(wav_full_path)

    # genera archivo de salida
    dirname, filename = crear_archivo_en_media_root("audio_asterisk/%Y/%m",
        "c{0}-{1}-".format(campana.id, uuid.uuid4().hex),
        settings.TMPL_FTS_AUDIO_CONVERSOR_EXTENSION)

    abs_output_filename = os.path.join(settings.MEDIA_ROOT, dirname, filename)
    assert os.path.exists(abs_output_filename)

    # convierte archivo
    convertir_audio(wav_full_path, abs_output_filename)

    # guarda ref. a archivo convertido
    campana.audio_asterisk = os.path.join(dirname, filename)
    campana.save()


def convertir_audio(input_file_abs, output_filename_abs):
    """Convierte archivo de audio de campaña.
    El archivo destino es creado en esta funcion.

    Parametros:
        input_file_abs: path a archivo de entrada (.wav)
        output_filename_abs: path a archivo de salida

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

    if not os.path.abspath(input_file_abs):
        logger.error("El archivo de salida no es un path absoluto: %s",
            output_filename_abs)
        raise FtsAudioConversionError("El archivo de salida no es "
            "un path absoluto")

    stdout_file = tempfile.TemporaryFile()
    stderr_file = tempfile.TemporaryFile()

    FTS_AUDIO_CONVERSOR = []
    for item in settings.TMPL_FTS_AUDIO_CONVERSOR:
        if item == "<INPUT_FILE>":
            FTS_AUDIO_CONVERSOR.append(input_file_abs)
        elif item == "<OUTPUT_FILE>":
            FTS_AUDIO_CONVERSOR.append(output_filename_abs)
        else:
            FTS_AUDIO_CONVERSOR.append(item)

    assert input_file_abs in FTS_AUDIO_CONVERSOR
    assert output_filename_abs in FTS_AUDIO_CONVERSOR

    # ejecutamos comando...
    try:
        logger.info("Iniciando conversion de audio de %s", input_file_abs)
        subprocess.check_call(FTS_AUDIO_CONVERSOR,
            stdout=stdout_file, stderr=stderr_file)
        logger.info("Conversion de audio finalizada exitosamente")

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
