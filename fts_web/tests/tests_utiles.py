# -*- coding: utf-8 -*-

"""
Tests del metodo 'fts_web.utiles'
"""

from __future__ import unicode_literals

import uuid
import logging as _logging

from django.conf import settings

from fts_web.tests.utiles import FTSenderBaseTest
from fts_web.utiles import (upload_to, get_class, crear_archivo_en_media_root,
                            elimina_espacios_parentesis_guiones)
from fts_web.errors import FtsError
import os

logger = _logging.getLogger(__name__)


class UtilesTest(FTSenderBaseTest):

    def assertAndSplit(self, text, prefix):
        tokens = text.split("/")
        self.assertEqual(tokens[0], prefix)
        self.assertEqual(tokens[1], "%Y")
        self.assertEqual(tokens[2], "%m")
        uuid.UUID(tokens[3][0:36])
        self.assertEqual(tokens[3][36], '-')
        return tokens[3][37:]

    def test_upload_to_audios_asterisk(self):
        upload_to_audios_asterisk = upload_to("audios_asterisk", 200)

        # ~~~~~ somefile.txt
        output = upload_to_audios_asterisk(None, "somefile.txt")
        self.assertEqual(self.assertAndSplit(output, "audios_asterisk"),
            'somefile.txt')

        # ~~~~~ ''
        output = upload_to_audios_asterisk(None, "")
        self.assertEqual(self.assertAndSplit(output, "audios_asterisk"), '')

        # ~~~~~ 'archivo con espacios#ext'
        output = upload_to_audios_asterisk(None, "archivo con espacios#ext")
        self.assertEqual(self.assertAndSplit(output, "audios_asterisk"),
            'archivoconespaciosext')

        # ~~~~~ file.extensionmuylarga
        len_sin_filename = len(upload_to_audios_asterisk(None, ""))
        largo_filename_max = 200 - len_sin_filename

        output = upload_to_audios_asterisk(None, "x" * 300)
        self.assertEqual(len(output), 200)
        rest_of_filename = self.assertAndSplit(output, "audios_asterisk")

        self.assertEqual(len(rest_of_filename), largo_filename_max)
        self.assertEqual(rest_of_filename, "x" * largo_filename_max)

    def test_crear_archivo_en_media_root(self):
        t_dirname = 'output-dir-name'
        t_filename_prefix = 'audio-converted-'

        dirname, filename = crear_archivo_en_media_root(
            t_dirname + '/algo', t_filename_prefix)
        logger.debug("crear_archivo_en_media_root():")
        logger.debug(" - %s", dirname)
        logger.debug(" - %s", filename)

        self.assertEqual(dirname, t_dirname + "/algo")
        self.assertTrue(filename.find(t_filename_prefix) >= 0)

        # ~~~ casi lo mismo, pero con 'suffix'
        dirname, filename = crear_archivo_en_media_root(
            t_dirname + '/algo', t_filename_prefix, suffix=".wav")

        logger.debug("crear_archivo_en_media_root():")
        logger.debug(" - %s", dirname)
        logger.debug(" - %s", filename)

        self.assertEqual(dirname, t_dirname + "/algo")
        self.assertTrue(filename.find(t_filename_prefix) >= 0)
        self.assertTrue(filename.endswith(".wav"))

    def test_crear_archivo_en_media_root_falla(self):
        dirname, filename = crear_archivo_en_media_root('algo', 'prefix')
        self.assertTrue(os.path.exists(settings.MEDIA_ROOT + "/" +
            dirname + "/" + filename))
        self.assertTrue(os.path.isfile(settings.MEDIA_ROOT + "/" +
            dirname + "/" + filename))
        self.assertTrue(os.path.isdir(settings.MEDIA_ROOT + "/" + dirname))

        with self.assertRaises(AssertionError):
            crear_archivo_en_media_root('/algo', 'prefix')

        with self.assertRaises(AssertionError):
            crear_archivo_en_media_root('algo/', 'prefix')

        with self.assertRaises(AssertionError):
            crear_archivo_en_media_root('algo', 'prefix/algomas')

    def test_get_class(self):
        # Testeamos que funcione con clase
        clazz = get_class("StringIO.StringIO")
        self.assertTrue(clazz)
        instance = clazz()
        self.assertFalse(instance.closed)

        # Testeamos q' reporte si la clase no existe
        try:
            get_class("StringIO.XxxxxxXxxxxx")
            self.fail("get_class() no genero excepcion")
        except FtsError as e:
            self.assertTrue(e.cause is not None)
            self.assertEquals(type(e.cause), AttributeError)

        # Testeamos q' reporte si el modulo no existe
        try:
            get_class("xxxxx.yyy.zzzz.XxxxxxXxxxxx")
            self.fail("get_class() no genero excepcion")
        except FtsError as e:
            self.assertTrue(e.cause is not None)
            self.assertEquals(type(e.cause), ImportError)

        # Testeamos nombre invalido
        try:
            get_class("xxxxx")
            self.fail("get_class() no genero excepcion")
        except FtsError as e:
            self.assertTrue(e.cause is None)

        # Testeamos nombre invalido
        try:
            get_class("")
            self.fail("get_class() no genero excepcion")
        except FtsError as e:
            self.assertTrue(e.cause is None)

        # Testeamos que funcione con func
        join_func = get_class("os.path.join")
        self.assertTrue(join_func)
        ret = join_func('a', 'b')
        self.assertEquals(ret, "a/b")

    def test_elimina_espacios_parentesis_guiones(self):
        cadena = elimina_espacios_parentesis_guiones(" asdfg32432 ñ(899) -781")
        self.assertEqual(cadena, "asdfg32432ñ899781")