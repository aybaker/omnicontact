# -*- coding: utf-8 -*-
"""
Implementacion de locks para sincronizar procesos de Celery.
"""

from __future__ import unicode_literals

import logging
import re
import socket


from fts_web import errors


logger = logging.getLogger(__name__)

REGEX_VALID_LOCK_NAME = re.compile(r'^[a-zA-Z0-9/\._-]+$')
"""Valid lock names can contain leters, numbers and
the characters / . - _
"""

LOCKS = {}
"""Dict with the created locks.
Key: lock name, Value: the socket.
"""

class LockingError(errors.FtsError):
    pass


def lock(lock_name):
    """
    Create a lock (using Unix Domain Socket).

    :param lock_name: name of the lock
    :raises: LockingError
    """

    assert isinstance(lock_name, (str, unicode))

    if not REGEX_VALID_LOCK_NAME.match(lock_name):
        raise LockingError(message="Nombre de lock invalido: '{0}'".format(lock_name))

    lock_socket = socket.socket(socket.AF_UNIX, socket.SOCK_DGRAM)
    logger.info("Se intentara obtener el lock '%s'", lock_name)
    try:
        lock_socket.bind('\x00' + lock_name)
        LOCKS[lock_name] = lock_socket
        logger.info("El lock '%s' se obtuvo con exito", lock_name)
    except socket.error:
        raise LockingError(message="No se pudo crear el lock '{0}'".format(lock_name))
