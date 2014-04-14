# -*- coding: utf-8 -*-

'''
Created on Apr 14, 2014

@author: Horacio G. de Oro
'''

from __future__ import unicode_literals
import tempfile
import subprocess
import logging as _logging
from fts_web.models import Campana
from django.core.files.storage import DefaultStorage
import os
from django.conf import settings
from fts_web.errors import FtsAudioConversionError


logger = _logging.getLogger(__name__)


def convertir_audio_de_campana(campana):
    """Convierte archivo de audio de campaña"""
    assert isinstance(campana, Campana)
    storage = DefaultStorage()
    storage.path(campana.reproduccion.name)

    # FIXME: implementar
    assert False, "IMPLEMENTAR"


def convertir_audio(input_file, output_file):
    """Convierte archivo de audio de campaña

    Parametros:
        input_file: path a archivo de entrada (.wav)
        output_file: path a archivo de salida (.gsm)

    Raises:
        FtsAudioConversionError: si se produjo algun tipo de error
    """

    if not os.path.exists(input_file):
        logger.error("El archivo de entrada no existe: %s", input_file)
        raise FtsAudioConversionError("El archivo de entrada no existe")

    if not os.path.abspath(input_file):
        logger.error("El archivo de entrada no es un path absoluto: %s",
            input_file)
        raise FtsAudioConversionError("El archivo de entrada no es "
            "un path absoluto")

    if os.path.exists(output_file):
        logger.error("El archivo de salida existe: %s", output_file)
        raise FtsAudioConversionError("El archivo de salida ya existe")

    stdout_file = tempfile.TemporaryFile()
    stderr_file = tempfile.TemporaryFile()

    FTS_AUDIO_CONVERSOR = []
    for item in settings.TMPL_FTS_AUDIO_CONVERSOR:
        if item == "<INPUT_FILE>":
            FTS_AUDIO_CONVERSOR.append(input_file)
        elif item == "<OUTPUT_FILE>":
            FTS_AUDIO_CONVERSOR.append(output_file)
        else:
            FTS_AUDIO_CONVERSOR.append(item)

    try:
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
