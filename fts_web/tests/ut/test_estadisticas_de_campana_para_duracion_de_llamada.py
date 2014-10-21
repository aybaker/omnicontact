# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import datetime
import json

from fts_web.models import Campana, DuracionDeLlamada
from fts_web.services.estadisticas_campana import (
    EstadisticasDeCampanaParaDuracionDeLlamadas)
from fts_web.tests.utiles import FTSenderBaseTest

from mock import Mock, create_autospec

"""
Este módulo testea el objeto EstadisticasDeCampanaParaDuracionDeLlamadas()
"""


class GenerarEstadisticasTests(FTSenderBaseTest):
    """
    Unit Test el método público
    EstadisticasDeCampanaParaDuracionDeLlamadas.generar_estadisticas()
    """

    def test_funciona_bien(self):

        campana = Campana(pk=1)
        campana.duracion_de_audio = '00:03:20'
        campana.save = Mock()

        queryset_emulado_duracion_de_llamadas = []
        for i in range(1, 5):
            duracion_de_llamada = DuracionDeLlamada(
                pk=i, campana=campana, numero_telefono='3513368309',
                fecha_hora_llamada=datetime.datetime.now(),
                duracion_en_segundos='00:03:20')
            queryset_emulado_duracion_de_llamadas.append(duracion_de_llamada)

        self.estadisticas_para_duracion_de_llamadas =\
            EstadisticasDeCampanaParaDuracionDeLlamadas()

        self.estadisticas_para_duracion_de_llamadas.\
            _obtener_duracion_de_llamada = Mock(
                return_value=queryset_emulado_duracion_de_llamadas)

        self.estadisticas_para_duracion_de_llamadas = Mock(
            spec_set=self.estadisticas_para_duracion_de_llamadas,
            wraps=self.estadisticas_para_duracion_de_llamadas)

        estadistica_para_reporte = json.dumps({
            "duracion_de_llamadas": {
                "no_escucharon_todo_el_mensaje": 0,
                "si_escucharon_todo_el_mensaje": 4,
            }})

        # -----

        self.estadisticas_para_duracion_de_llamadas.generar_estadisticas(
            campana)

        self.assertEqual(campana.metadata_estadisticas,
                         estadistica_para_reporte)
