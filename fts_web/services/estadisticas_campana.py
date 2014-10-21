# -*- coding: utf-8 -*-

"""
Servicio encargado de calcular estadisticas y generar graficos
para la web.
"""

from __future__ import unicode_literals

from collections import defaultdict
import logging
import pygal
import json
import datetime
import re

from fts_web.models import (AgregacionDeEventoDeContacto, Campana,
                            DuracionDeLlamada)
from pygal.style import Style


logger = logging.getLogger(__name__)

ESTILO_VERDE_ROJO_NARANJA = Style(
    background='transparent',
    plot_background='transparent',
    foreground='#555',
    foreground_light='#555',
    foreground_dark='#555',
    opacity='1',
    opacity_hover='.6',
    transition='400ms ease-in',
    colors=('#5cb85c', '#d9534f', '#f0ad4e')
)

ESTILO_MULTICOLOR = Style(
    background='transparent',
    plot_background='transparent',
    foreground='#555',
    foreground_light='#555',
    foreground_dark='#555',
    opacity='1',
    opacity_hover='.6',
    transition='400ms ease-in',
    colors=('#428bca', '#5cb85c', '#5bc0de', '#f0ad4e', '#d9534f',
        '#a95cb8', '#5cb8b5', '#caca43', '#96ac43', '#ca43ca')
)


class EstadisticasCampanaService(object):

    def _calcular_estadisticas(self, campana, tipo_agregacion):
        """
        Este método devuelve las estadísticas de
        la campaña actual.
        """

        # FIXME: mover este assert de nuevo a Campana
        assert campana.estado in (Campana.ESTADO_ACTIVA,
                                  Campana.ESTADO_PAUSADA,
                                  Campana.ESTADO_DEPURADA)

        dic_totales = AgregacionDeEventoDeContacto.objects.procesa_agregacion(
            campana.pk, campana.cantidad_intentos, tipo_agregacion)

        total_contactos = dic_totales['total_contactos']
        if not total_contactos > 0:
            return None

        # Generales
        total_atentidos = dic_totales['total_atentidos']
        porcentaje_atendidos = (100.0 * float(total_atentidos) /
            float(total_contactos))

        total_no_atendidos = dic_totales['total_no_atendidos']
        porcentaje_no_atendidos = (100.0 * float(total_no_atendidos) /
            float(total_contactos))

        total_no_llamados = dic_totales['total_no_llamados']
        porcentaje_no_llamados = (100.0 * float(total_no_llamados) /
            float(total_contactos))

        # Atendidos en cada intento.
        total_atendidos_intentos = dic_totales['total_atendidos_intentos']

        # Cantidad por opción.
        opcion_x_cantidad = defaultdict(lambda: 0)
        opcion_x_porcentaje = defaultdict(lambda: 0)
        opcion_invalida_x_cantidad = defaultdict(lambda: 0)
        opcion_invalida_x_porcentaje = defaultdict(lambda: 0)
        opcion_valida_x_cantidad = defaultdict(lambda: 0)
        opcion_valida_x_porcentaje = defaultdict(lambda: 0)
        if dic_totales['total_opciones'] > 0:
            opciones_campana = [opcion.digito for opcion in\
                campana.opciones.all()]
            for opcion in range(10):
                cantidad_opcion = dic_totales['total_opcion_{0}'.format(
                    opcion)]
                opcion_x_cantidad[opcion] = cantidad_opcion
                opcion_x_porcentaje[opcion] = (100.0 * float(cantidad_opcion) /
                    float(dic_totales['total_opciones']))
                if not opcion in opciones_campana:
                    opcion_invalida_x_cantidad[opcion] = cantidad_opcion
                    opcion_invalida_x_porcentaje[opcion] = (100.0 *
                        float(cantidad_opcion) /
                        float(dic_totales['total_opciones']))
                else:
                    opcion_valida_x_cantidad[opcion] = cantidad_opcion
                    opcion_valida_x_porcentaje[opcion] = (100.0 *
                        float(cantidad_opcion) /
                        float(dic_totales['total_opciones']))

        dic_estadisticas = {
            # Estadísticas Generales.
            'total_contactos': total_contactos,

            'total_atentidos': total_atentidos,
            'porcentaje_atendidos': porcentaje_atendidos,
            'total_no_atentidos': total_no_atendidos,
            'porcentaje_no_atendidos': porcentaje_no_atendidos,
            'total_no_llamados': total_no_llamados,
            'porcentaje_no_llamados': porcentaje_no_llamados,
            'porcentaje_avance': dic_totales['porcentaje_avance'],
            'total_atendidos_intentos': total_atendidos_intentos,

            # Estadisticas de las llamadas Contestadas.
            'opcion_x_cantidad': dict(opcion_x_cantidad),
            'opcion_x_porcentaje': dict(opcion_x_porcentaje),
            'opcion_invalida_x_cantidad': dict(opcion_invalida_x_cantidad),
            'opcion_invalida_x_porcentaje': dict(opcion_invalida_x_porcentaje),
            'opcion_valida_x_cantidad': dict(opcion_valida_x_cantidad),
            'opcion_valida_x_porcentaje': dict(opcion_valida_x_porcentaje),
        }

        return dic_estadisticas

    def obtener_estadisticas_render_graficos_supervision(self, campana):
        estadisticas = self._calcular_estadisticas(campana,
            AgregacionDeEventoDeContacto.TIPO_AGREGACION_SUPERVISION)

        if estadisticas:
            # Torta: porcentajes de opciones selecionadas.
            opcion_valida_x_porcentaje = estadisticas[
                'opcion_valida_x_porcentaje']
            opcion_invalida_x_porcentaje = estadisticas[
                'opcion_invalida_x_porcentaje']

            no_data_text = "No se han seleccionado opciones"
            torta_opcion_x_porcentaje = pygal.Pie(# @UndefinedVariable
                style=ESTILO_MULTICOLOR,
                legend_at_bottom=True,
                no_data_text=no_data_text,
                no_data_font_size=32,
                legend_font_size=25,
                truncate_legend=10,
                tooltip_font_size=30,
            )
            torta_opcion_x_porcentaje.title = 'Porcentajes de opciones.'

            opciones_dict = dict([(op.digito, op.get_descripcion_de_opcion())
                for op in campana.opciones.all()])
            for opcion, porcentaje in opcion_valida_x_porcentaje.items():
                torta_opcion_x_porcentaje.add(opciones_dict[opcion],
                    porcentaje)

            porcentaje_opciones_invalidas = 0
            for porcentaje in opcion_invalida_x_porcentaje.values():
                porcentaje_opciones_invalidas += porcentaje
            if porcentaje_opciones_invalidas:
                torta_opcion_x_porcentaje.add('Inválidas',
                    porcentaje_opciones_invalidas)

            return {
                    'estadisticas': estadisticas,
                    'torta_opcion_x_porcentaje': torta_opcion_x_porcentaje,
            }
        else:
            logger.info("Campana %s NO obtuvo estadísticas.", campana.id)

    def obtener_estadisticas_render_graficos_reportes(self, campana):

        # FIXME: mover este assert de nuevo a Campana
        assert campana.estado == Campana.ESTADO_DEPURADA, \
            "Solo se generan reportes de campanas depuradas"

        estadisticas = self._calcular_estadisticas(campana,
            AgregacionDeEventoDeContacto.TIPO_AGREGACION_REPORTE)

        if estadisticas:
            logger.info("Generando grafico para campana %s", campana.id)

            # Torta: porcentajes de contestados, no contestados y no llamados.
            torta_general = pygal.Pie(# @UndefinedVariable
                style=ESTILO_VERDE_ROJO_NARANJA)
            # torta_general.title = 'Porcentajes Generales de {0} contactos.'.\
            #    format(estadisticas['total_contactos'])
            torta_general.title = "Resultado de llamadas"
            torta_general.add('Atendidas', estadisticas[
                'porcentaje_atendidos'])

            torta_general.add('No Atendidas', estadisticas[
                'porcentaje_no_atendidos'])
            torta_general.add('Sin Llamar', estadisticas[
                'porcentaje_no_llamados'])

            # Torta: porcentajes de opciones selecionadas.
            no_data_text = "No se han seleccionado opciones"
            dic_opcion_x_porcentaje = estadisticas['opcion_x_porcentaje']
            torta_opcion_x_porcentaje = pygal.Pie(# @UndefinedVariable
                style=ESTILO_MULTICOLOR,
                legend_at_bottom=True,
                no_data_text=no_data_text,
                no_data_font_size=32
            )
            torta_opcion_x_porcentaje.title = 'Opciones seleccionadas'

            opciones_dict = dict([(op.digito, op.get_descripcion_de_opcion())
                for op in campana.opciones.all()])

            porcentaje_invalidas = 0
            for opcion, porcentaje in dic_opcion_x_porcentaje.items():
                try:
                    torta_opcion_x_porcentaje.add(opciones_dict[opcion],
                        porcentaje)
                except KeyError:
                    porcentaje_invalidas += porcentaje

            torta_opcion_x_porcentaje.add(
                '#Inválidas', porcentaje_invalidas)

            # Barra: Total de llamados atendidos en cada intento.
            total_atendidos_intentos = estadisticas['total_atendidos_intentos']
            intentos = [total_atendidos_intentos[intentos] for intentos, _ in\
                total_atendidos_intentos.items()]
            barra_atendidos_intentos = pygal.Bar(# @UndefinedVariable
                show_legend=False,
                style=ESTILO_MULTICOLOR)
            barra_atendidos_intentos.title = 'Cantidad de llamadas atendidas en\
                cada intento.'
            barra_atendidos_intentos.x_labels = map(str, range(1,
                len(total_atendidos_intentos) + 1))
            barra_atendidos_intentos.add('Cantidad', intentos)

            return {
                'estadisticas': estadisticas,
                'torta_general': torta_general,
                'torta_opcion_x_porcentaje': torta_opcion_x_porcentaje,
                'barra_atendidos_intentos': barra_atendidos_intentos,
            }
        else:
            logger.info("Campana %s NO obtuvo estadísticas.", campana.id)


# =============================================================================
# Nuevos objetos para el cálculo de estadísticas para reportes
# =============================================================================

class EstadisticasDeCampanaParaReporteServiceV2(object):
    """
    Nuevo objeto encargado de los cálculos de las estadísticas necesarias para
    los diferentes reportes.
    Este objeto es accedido en el momento de depuración de la campana
    referida después del cálculos de las DuracionDeLlamada de la misma.
    """

    def __init__(self):
        self._estadisticas_para_duracion_de_llamada = \
            EstadisticasDeCampanaParaDuracionDeLlamadas()

    def procesar_estadisticas(self, campana):
        self._estadisticas_para_duracion_de_llamada.generar_estadisticas(
            campana)


class EstadisticasDeCampanaParaDuracionDeLlamadas(object):
    """
    Obtiene, calcula y guarda en Campana los datos estadísticos para las
    duraciones de las llamadas de una campana pasada por parámetro.
    """

    def _obtener_duracion_de_llamada(self, campana):
        return DuracionDeLlamada.objects.obtener_objetos_de_una_campana(
            campana)

    def _calcular_estadisticas(self, duracion_de_audio, duracion_de_llamadas):
        cantidad_no_escucharon_todo = 0
        cantidad_escucharon_todo = 0

        for duracion_de_llamada in duracion_de_llamadas:
            duracion_de_audio_en_segundos = getSec(
                duracion_de_audio.isoformat())

            if (duracion_de_audio_en_segundos
               < duracion_de_llamada.duracion_en_segundos):
                cantidad_no_escucharon_todo += 1
            else:
                cantidad_escucharon_todo += 1

        return json.dumps({
            "duracion_de_llamadas": {
                "no_escucharon_todo_el_mensaje": cantidad_no_escucharon_todo,
                "si_escucharon_todo_el_mensaje": cantidad_escucharon_todo,
            }
        })

    def _guardar_estadisticas(self, campana, estadisticas_calculadas):
        campana.metadata_estadisticas = estadisticas_calculadas
        campana.save()

    def generar_estadisticas(self, campana):
        """
        Se encarga de guardar en Campana el cálculo de las estadísticas para
        la duración de las llamadas de la campana.
        """

        duracion_de_llamadas = \
            self._obtener_duracion_de_llamada(campana)

        estadisticas_calculadas = self._calcular_estadisticas(
            campana.duracion_de_audio, duracion_de_llamadas)

        self._guardar_estadisticas(campana, estadisticas_calculadas)


def getSec(s):
    """
    Solución barata de Stackoverflow:
    http://stackoverflow.com/questions/6402812/how-to-convert-an-hmmss-time-string-to-seconds-in-python
    """
    l = s.split(':')
    return int(l[0]) * 3600 + int(l[1]) * 60 + int(l[2])
