# -*- coding: utf-8 -*-

"""
    Este modulo testea el servicio PredictoMetadagtaService
"""

from __future__ import unicode_literals

from django.test.utils import override_settings
from fts_web.models import BaseDatosContacto
from fts_web.services.base_de_datos_contactos import PredictorMetadataService
from fts_web.tests.utiles import FTSenderBaseTest, get_test_resource_directory
from fts_web.parser import ParserCsv
from fts_web.utiles import ValidadorDeNombreDeCampoExtra
import logging as logging_


logger = logging_.getLogger(__name__)


class PredictorBaseDatosContactoTests(FTSenderBaseTest):
    """Unit tests de PreditorMetadataService"""

    @override_settings(MEDIA_ROOT=get_test_resource_directory())
    def test_inferir_metadata_correctamente(self):

        planilla = self.get_test_resource("planilla-ejemplo-10.csv")
        nombre_archivo = "planilla-ejemplo-10.csv"
        base_test = BaseDatosContacto.objects.create(nombre="test",
            archivo_importacion=planilla,
            nombre_archivo_importacion=nombre_archivo, metadata="")

        parser = ParserCsv()
        estructura_archivo = parser.previsualiza_archivo(base_test)

        predictor_metadata = PredictorMetadataService()
        metadata = predictor_metadata.inferir_metadata_desde_lineas(
            estructura_archivo)

        validador_nombre = ValidadorDeNombreDeCampoExtra()
        for nombre_columna in metadata.nombres_de_columnas:
            self.assertTrue(validador_nombre.validar_nombre_de_columna(
                nombre_columna), "el nombre de columna es invalido")
