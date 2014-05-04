# -*- coding: utf-8 -*-

"""Tests del modulo fts_web.errors"""

from __future__ import unicode_literals

from fts_web.errors import FtsAudioConversionError
from fts_web.tests.utiles import FTSenderBaseTest


class ErrorsTest(FTSenderBaseTest):

    def test_exceptions(self):
        try:
            raise FtsAudioConversionError()
        except FtsAudioConversionError as e:
            self.assertEqual(str(e), "")

        try:
            raise FtsAudioConversionError("mensaje")
        except FtsAudioConversionError as e:
            self.assertEqual(str(e), "mensaje")

        try:
            try:
                {}['err']
            except KeyError as keyerr:
                raise FtsAudioConversionError("mensaje")
        except FtsAudioConversionError as e:
            self.assertEqual(str(e), "mensaje")

        try:
            try:
                {}['err']
            except KeyError as keyerr:
                raise FtsAudioConversionError("mensaje", cause=keyerr)
        except FtsAudioConversionError as e:
            self.assertEqual(str(e), "mensaje (caused by "
                "<type 'exceptions.KeyError'>: u'err')")

        try:
            try:
                list()[1]
            except IndexError as err:
                raise FtsAudioConversionError("mensaje", cause=err)
        except FtsAudioConversionError as e:
            self.assertEqual(str(e), "mensaje (caused by "
                "<type 'exceptions.IndexError'>: list index out of range)")
