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
from django.core.files import File
from django.core.files.storage import default_storage
from fts_web.errors import FtsAudioConversionError
from fts_web.models import Campana, upload_to_audios_asterisk
import logging as _logging
from fts_web.utiles import resolve_strftime


logger = _logging.getLogger(__name__)


def convertir_audio_de_campana(campana):
    """Convierte archivo de audio de campaña,
    y actualiza la instancia de campaña
    """
    assert isinstance(campana, Campana)

    wav_full_path = default_storage.path(campana.reproduccion.name)
    assert os.path.exists(wav_full_path)

    relative_filename = resolve_strftime(upload_to_audios_asterisk(campana,
        'convertido-campana-{0}.gsm'.format(campana.id)))
    output_directory_rel, prefix = os.path.split(relative_filename)
    output_directory = os.path.join(settings.MEDIA_ROOT, output_directory_rel)

    if not os.path.exists(output_directory):
        os.makedirs(output_directory)

    _, output_filename = tempfile.mkstemp(
        dir=output_directory, prefix=prefix)

    try:
        convertir_audio(wav_full_path, output_filename, overwrite=True)
        campana.audio_asterisk = relative_filename
        campana.save()
    except:
        # En caso de error, borramos output
        os.remove(output_filename)
        raise


def convertir_audio(input_file, output_file, overwrite=False):
    """Convierte archivo de audio de campaña

    Parametros:
        input_file: path a archivo de entrada (.wav)
        output_file: path a archivo de salida (.gsm)

    Raises:
        FtsAudioConversionError: si se produjo algun tipo de error
    """

    # chequeos...
    if not os.path.exists(input_file):
        logger.error("El archivo de entrada no existe: %s", input_file)
        raise FtsAudioConversionError("El archivo de entrada no existe")

    if not os.path.abspath(input_file):
        logger.error("El archivo de entrada no es un path absoluto: %s",
            input_file)
        raise FtsAudioConversionError("El archivo de entrada no es "
            "un path absoluto")

    if overwrite == False and os.path.exists(output_file):
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

    assert input_file in FTS_AUDIO_CONVERSOR
    assert output_file in FTS_AUDIO_CONVERSOR

    # ejecutamos comando...
    try:
        logger.info("Iniciando conversion de audio de %s", input_file)
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
