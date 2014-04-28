# -*- coding: utf-8 -*-

'''
Created on Apr 15, 2014

@author: Horacio G. de Oro
'''

from __future__ import unicode_literals
import re
import time
import uuid
import os

from fts_web.errors import FtsError

from django.conf import settings

import logging as _logging
import tempfile

logger = _logging.getLogger('poll_daemon')

SUBSITUTE_REGEX = re.compile(r'[^a-z\._-]')


def _upload_to(prefix, max_length, instance, filename):
    filename = SUBSITUTE_REGEX.sub('', filename)
    return "{0}/%Y/%m/{1}-{2}".format(prefix,
        str(uuid.uuid4()), filename)[:max_length]


def upload_to(prefix, max_length):
    """Genera (devuelve) una funcion a ser usada en `upload_to` de `FileField`.
    La funcion generada genera un path (relativo) de no mas de `max_length`
    caracteres, y usando el prefijo `prefix`
    """
    def func(instance, filename):
        return _upload_to(prefix, max_length, instance, filename)
    return func


def resolve_strftime(text):
    """Ejecuta strftime() en texto pasado por parametro"""
    return time.strftime(text)  # time.gmtime()


def crear_archivo_en_media_root(filename_template):
    """Crea un archivo en el directorio MEDIA_ROOT. Si los directorios
    no existen, los crea tambien.

    Para la creacion del archivo usa `tempfile.mkstemp`

    Ej:
        crear_archivo('data/%Y/%m/audio-original'):
            En este caso, se creara (si no existen) los
            directorios `data`, ANIO y MES, y `audio-original`
            es parte del prefijo del archivo.

        El prefijo del nombre de archivo es OBLIGATORIO, por lo tanto,
            `filename_template` NO puede finalizar en '/'

    Devuelve: tupla con
        (directorio_relativo_a_MEDIA_ROOT, nombre_de_archivo)
    """
    assert filename_template[-1] != '/'

    relative_filename = resolve_strftime(filename_template)
    output_directory_rel, tempfile_prefix = os.path.split(relative_filename)
    output_directory_abs = os.path.join(
        settings.MEDIA_ROOT, output_directory_rel)

    if not os.path.exists(output_directory_abs):
        os.makedirs(output_directory_abs)

    _, output_filename = tempfile.mkstemp(
        dir=output_directory_abs, prefix=tempfile_prefix)

    return output_directory_rel, os.path.split(output_filename)[1]


# TODO: rename to 'get_class_or_func'
def get_class(full_name):
    """Devuelve clase  o func referenciada por `full_name`"""
    splitted = full_name.split(r".")
    if len(splitted) < 2:
        raise FtsError("La clase/func sepecificada no es valida: '{0}'".format(
            full_name))
    module_name = ".".join(splitted[0:-1])
    class_or_func_name = splitted[-1]

    try:

        try:
            module = __import__(module_name)
        except ImportError as e:
            msg = "No se pudo importar el modulo '{0}'".format(module_name)
            logger.warn(msg)
            raise FtsError(msg, e)

        for sub_module_name in splitted[1:-1]:
            module = getattr(module, sub_module_name)

        try:
            clazz = getattr(module, class_or_func_name)
        except AttributeError as e:
            msg = "El modulo '{0}' no posee la clase o func '{1}'".format(
                module_name, class_or_func_name)
            logger.warn(msg)
            raise FtsError(msg, e)

    except FtsError:
        raise

    except Exception as e:
        msg = "No se pudo obtener la clase o func '{0}'".format(full_name)
        logger.warn(msg)
        raise FtsError(msg, e)

    return clazz
