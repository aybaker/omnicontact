# -*- coding: utf-8 -*-

"""Unittests del modelo Campana"""

from __future__ import unicode_literals

import json

from fts_web.models import BaseDatosContacto
from fts_web.tests.utiles import FTSenderBaseTest


class TestMetadataBaseDatosContacto(FTSenderBaseTest):
    """Clase para testear MetadataBaseDatosContacto"""

    def test_parsea_datos_correctos(self):
        bd = BaseDatosContacto()
        bd.metadata = json.dumps({'col_telefono': 6})
        metadata = bd.get_metadata()

        self.assertEqual(metadata.columna_con_telefono, 6)

    def test_guarda_datos_correctos(self):
        bd = BaseDatosContacto()
        bd.metadata = json.dumps({'col_telefono': 6})
        metadata = bd.get_metadata()

        metadata.columna_con_telefono = 123
        metadata.save()

        self.assertDictEqual(json.loads(bd.metadata), {'col_telefono': 123})

    def test_genera_valueerror_sin_datos(self):
        with self.assertRaises(ValueError):
            BaseDatosContacto().get_metadata().columna_con_telefono
