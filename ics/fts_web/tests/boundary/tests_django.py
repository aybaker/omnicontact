# -*- coding: utf-8 -*-

"""Tests comportamiento de Djagno"""

from __future__ import unicode_literals
from fts_web.tests.utiles import FTSenderBaseTest
from django.utils.encoding import force_text


class TestForceText(FTSenderBaseTest):

    def test_ascii(self):
        text = force_text(b'hola', errors='ignore')
        self.assertTrue(type(text) == unicode)
        self.assertEqual(text, u'hola')

    def test_utf8(self):
        text = force_text(b'hol\xc3\xa1', errors='ignore')
        self.assertTrue(type(text) == unicode)
        self.assertEqual(text, u'holá')

    def test_iso_8859_2(self):
        text = force_text(b'hol\xe1', errors='ignore')
        self.assertTrue(type(text) == unicode)
        self.assertEqual(text, u'hol')

    def test_unicode(self):
        text = force_text(u'holá')
        self.assertTrue(type(text) == unicode)
        self.assertEqual(text, u'holá')

    def test_unicode_errors_ignore(self):
        text = force_text(u'holá', errors='ignore')
        self.assertTrue(type(text) == unicode)
        self.assertEqual(text, u'holá')

    def test_unicode_errors_replace(self):
        text = force_text(u'holá', errors='replace')
        self.assertTrue(type(text) == unicode)
        self.assertEqual(text, u'holá')

    def test_int(self):
        text = force_text(123, errors='replace')
        self.assertTrue(type(text) == unicode)
        self.assertEqual(text, u'123')

    def test_none(self):
        text = force_text(None, errors='replace')
        self.assertTrue(type(text) == unicode)
        self.assertEqual(text, u'None')

    def test_clazz(self):
        text = force_text(TestForceText, errors='replace')
        self.assertTrue(type(text) == unicode)
        class_str = (u"<class "
                     "'fts_web.tests.boundary.tests_django.TestForceText'>")
        self.assertEqual(text, class_str)
