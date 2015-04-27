# -*- coding: utf-8 -*-

"""
Test de integracion de la creación de BD de contactos desde archivos CSV.
"""

from __future__ import unicode_literals

import logging as _logging

from django.test.utils import override_settings

from fts_web.models import BaseDatosContacto, Contacto
from fts_web.parser import ParserCsv
from fts_web.services.base_de_datos_contactos import PredictorMetadataService, CreacionBaseDatosService
from fts_web.tests.utiles import FTSenderBaseTest, get_test_resource_directory


logger = _logging.getLogger(__name__)


class TestWorkflowCreacionBdContactoDesdeCsv(FTSenderBaseTest):

    @override_settings(MEDIA_ROOT=get_test_resource_directory())
    def test_con_planilla_ejemplo_6(self):
        bd_contacto = BaseDatosContacto.objects.create(
            nombre="base-datos-contactos",
            archivo_importacion=self.get_test_resource("planilla-ejemplo-6.csv"),
            nombre_archivo_importacion='planilla-ejemplo-6.csv')

        parser = ParserCsv()
        estructura_archivo = parser.previsualiza_archivo(bd_contacto)
        predictor_metadata = PredictorMetadataService()
        metadata_inferida = predictor_metadata.inferir_metadata_desde_lineas(
            estructura_archivo)

        metadata = bd_contacto.get_metadata()
        metadata._metadata = metadata_inferida._metadata
        metadata.nombres_de_columnas = ["TELEFONO", "NOMBRE", "FECHA", "HORA"]
        metadata.save()

        creacion_base_datos_service = CreacionBaseDatosService()
        creacion_base_datos_service.importa_contactos(bd_contacto)
        creacion_base_datos_service.define_base_dato_contacto(bd_contacto)

        # ----- checks

        self.assertEquals(BaseDatosContacto.objects.get(pk=bd_contacto.id).estado,
                          BaseDatosContacto.ESTADO_DEFINIDA,
                          "La BD no ha quedado en estado ESTADO_DEFINIDA")

        nros_telefono = [contacto.obtener_telefono_y_datos_extras(metadata)[0]
                         for contacto in Contacto.objects.filter(bd_contacto=bd_contacto.id)]

        self.assertEquals(len(nros_telefono), 3, "Deberia haber 3 contactos")

        self.assertEquals(set(nros_telefono),
                          set(['354303459865', '111534509230', '283453013491']),
                          "Deberia haber 3 contactos")

    @override_settings(MEDIA_ROOT=get_test_resource_directory())
    def test_con_demas_planillas_de_ejemplo(self):

        PLANILLAS = (
            # "planilla-ejemplo-0.csv",
            "planilla-ejemplo-1.csv",
            # "planilla-ejemplo-2.csv",
            # "planilla-ejemplo-3.csv",
            "planilla-ejemplo-4.csv",
            # "planilla-ejemplo-5.csv",
        )

        for planilla in PLANILLAS:
            logger.debug("Procesando planilla %s", planilla)
            bd_contacto = BaseDatosContacto.objects.create(
                nombre="base-datos-contactos-{0}".format(planilla),
                archivo_importacion=self.get_test_resource(planilla),
                nombre_archivo_importacion=planilla)

            parser = ParserCsv()
            estructura_archivo = parser.previsualiza_archivo(bd_contacto)
            predictor_metadata = PredictorMetadataService()
            metadata_inferida = predictor_metadata.inferir_metadata_desde_lineas(
                estructura_archivo)

            metadata = bd_contacto.get_metadata()
            metadata._metadata = metadata_inferida._metadata
            metadata.nombres_de_columnas = ["COL{0}".format(num)
                                            for num in range(metadata.cantidad_de_columnas)]
            metadata.save()

            creacion_base_datos_service = CreacionBaseDatosService()
            creacion_base_datos_service.importa_contactos(bd_contacto)
            creacion_base_datos_service.define_base_dato_contacto(bd_contacto)

            # ----- checks

            self.assertEquals(BaseDatosContacto.objects.get(pk=bd_contacto.id).estado,
                              BaseDatosContacto.ESTADO_DEFINIDA,
                              "La BD generada desde '{0}' NO ha quedado en estado ESTADO_DEFINIDA"
                              "".format(planilla))

            self.assertTrue(Contacto.objects.filter(bd_contacto=bd_contacto.id).count() > 0,
                            "La BD generada desde '{0}' NO posee contactos".format(planilla))
