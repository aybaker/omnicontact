# -*- coding: utf-8 -*-

"""Tests del modulo fts_daemon.locks"""

from __future__ import unicode_literals


import os
import random


from fts_daemon.locks import lock
from fts_daemon.locks import LockingError
from fts_daemon.locks import LOCKS
from fts_web.tests.utiles import FTSenderBaseTest


class LockTest(FTSenderBaseTest):

    PREFIJO = 'fts.unittest.{0}.{1}.'.format(os.getpid(), random.randint(100, 999))

    def lock(self, lock_name):
        """Crea lock con un prefijo que cambia con cada ejecucion
        del unittest, pero genera los mismos nombres dentro de la misma ejecucion.
        """
        lock_name = self.PREFIJO + lock_name
        return lock(lock_name)

    def test_fails_with_invalid_names(self):
        with self.assertRaises(LockingError):
            self.lock('nombre de lock contiene espacios')

        with self.assertRaises(LockingError):
            self.lock('nombre.de.lock.contiene.&.ampersand')

        with self.assertRaises(LockingError):
            self.lock('nombre.de.lock.contiene.%.porciento')

        with self.assertRaises(LockingError):
            self.lock('nombre.de.lock.contiene.\\.barra')

        with self.assertRaises(LockingError):
            self.lock('nombre.de.lock.contiene.ñ.enie')

    def test_success_with_valid_names(self):
        self.lock('nombre.simple')
        self.lock('nombre.SIMPLE')
        self.lock('nombre.SIMPLE.y.123.numeros')
        self.lock('nombre.SIMPLE.y.guion-medio')
        self.lock('nombre.SIMPLE.y.guion_bajo')
        self.lock('nombre.SIMPLE.y.con/barra')
        self.lock('nombre.CON_t0d4s/los-c4r4ct3r3s_Valid0S')

    def test_fail_lock_twice(self):
        lock_name = 'lockear.dos.veces'
        initial_lock_count = len(LOCKS)

        # Creamos lock, chequeamos q' se haya agregado 1
        self.lock(lock_name)
        self.assertEquals(len(LOCKS), initial_lock_count + 1)

        # Intentamos nuevamente, chequeamos q' NO se haya agregado otro
        with self.assertRaises(LockingError):
            self.lock(lock_name)
        self.assertEquals(len(LOCKS), initial_lock_count + 1)

    def test_lock_es_guardado_cuando_es_creado_exitosamente(self):
        lock_name = 'test_lock_es_guardado_cuando_es_creado_exitosamente'
        initial_lock_count = len(LOCKS)

        self.lock(lock_name)
        self.assertEquals(len(LOCKS), initial_lock_count + 1)

    def test_lock_no_es_guardado_cuando_falla_su_creacion(self):
        lock_name = '$$$test_lock_no_es_guardado_cuando_falla_su_creacion$$$'
        initial_lock_count = len(LOCKS)

        with self.assertRaises(LockingError):
            self.lock(lock_name)
        self.assertEquals(len(LOCKS), initial_lock_count)
