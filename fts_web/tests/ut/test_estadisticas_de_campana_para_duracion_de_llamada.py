# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import datetime
import json

from fts_web.models import Campana, DuracionDeLlamada
from fts_web.services.estadisticas_campana import (
    EstadisticasDeCampanaParaDuracionDeLlamadas)
from fts_web.tests.utiles import FTSenderBaseTest

from mock import Mock

"""
Este módulo testea el objeto EstadisticasDeCampanaParaDuracionDeLlamadas()
"""


class GenerarEstadisticasTests(FTSenderBaseTest):
    """
    Unit Test el método público
    EstadisticasDeCampanaParaDuracionDeLlamadas.generar_estadisticas()
    """

    def test_funciona_bien_con_2_llamadas_escuchadas_y_dos_no(self):

        campana = Campana(pk=1)
        campana.duracion_de_audio = datetime.time(0, 3, 20)
        campana.save = Mock()

        queryset_emulado_duracion_de_llamadas = []
        for i in range(1, 5):
            # Las dos primeras DuracionDeLlamada duran (188" y 189") lo que
            # no se contemplan como escuchadas, debido al margen de 5%.
            # La duración del audio de campana es de 00:03:20 (200").
            duracion_en_segundos = 187 + i

            duracion_de_llamada = DuracionDeLlamada(
                pk=i, campana=campana, numero_telefono='3513368309',
                fecha_hora_llamada=datetime.datetime.now(),
                duracion_en_segundos=duracion_en_segundos)

            queryset_emulado_duracion_de_llamadas.append(duracion_de_llamada)

        self.estadisticas_para_duracion_de_llamadas =\
            EstadisticasDeCampanaParaDuracionDeLlamadas()

        self.estadisticas_para_duracion_de_llamadas.\
            _obtener_duracion_de_llamada = Mock(
                return_value=queryset_emulado_duracion_de_llamadas)

        self.estadisticas_para_duracion_de_llamadas = Mock(
            spec_set=self.estadisticas_para_duracion_de_llamadas,
            wraps=self.estadisticas_para_duracion_de_llamadas)

        # -----

        self.estadisticas_para_duracion_de_llamadas.generar_estadisticas(
            campana)

        self.assertEqual(campana.estadisticas,
                         json.dumps({"duracion_de_llamadas": {
                                    "no_escucharon_todo_el_mensaje": 2,
                                    "si_escucharon_todo_el_mensaje": 2}}))
