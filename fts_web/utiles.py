# -*- coding: utf-8 -*-

'''
Created on Apr 15, 2014

@author: Horacio G. de Oro
'''

from __future__ import unicode_literals
import re
import time
import uuid

from fts_web.errors import FtsError

from django.conf import settings

import logging as _logging

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


def get_class(full_class_name):
    """Devuelve clase referenciada por `full_class_name`"""
    splitted = full_class_name.split(r".")
    if len(splitted) < 2:
        raise FtsError("La clase sepecificada no es valida: '{0}'".format(
            full_class_name))
    module_name = ".".join(splitted[0:-1])
    class_name = splitted[-1]

    try:

        try:
            module = __import__(module_name)
        except ImportError as e:
            msg = "No se pudo importar el modulo '{0}'".format(module_name)
            logger.warn(msg)
            raise FtsError(msg, e)

        try:
            clazz = getattr(module, class_name)
        except AttributeError as e:
            msg = "El modulo '{0}' no posee la clase '{1}'".format(
                module_name, class_name)
            logger.warn(msg)
            raise FtsError(msg, e)

    except FtsError:
        raise

    except Exception as e:
        msg = "No se pudo obtener la clase '{0}'".format(full_class_name)
        logger.warn(msg)
        raise FtsError(msg, e)

    return clazz
