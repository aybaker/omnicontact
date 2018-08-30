# -*- coding: utf-8 -*-

"""
Servicio encargado de calcular estadisticas y generar graficos
para la web.
"""

from __future__ import unicode_literals

from collections import defaultdict
import pygal
import json
from pygal.style import Style

from django.db import connection
from django.conf import settings

from fts_web.models import (AgregacionDeEventoDeContacto, Campana,
                            DuracionDeLlamada)
from fts_daemon.models import EventoDeContacto
from fts_web.utiles import log_timing
import logging as _logging

logger = _logging.getLogger(__name__)

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


    def _obtener_total_no_atendidos_por_evento(self, listado):
        """
        Se encarga de obtener los contadores de ciertos eventos(ocupados,
        no answer, canal no disponible, congestion)

        :param listado: por cada contacto de la campana me trae un array 
        con los eventos.
        :return me retorna un diccionario con los 4 contadores de los 
        eventos mencionados 
        """
        finalizadores = EventoDeContacto.objects.get_eventos_finalizadores()

        counter_por_evento = {
            EventoDeContacto.EVENTO_ASTERISK_DIALSTATUS_BUSY: 0,
            EventoDeContacto.EVENTO_ASTERISK_DIALSTATUS_NOANSWER: 0,
            EventoDeContacto.EVENTO_ASTERISK_DIALSTATUS_CHANUNAVAIL: 0,
            EventoDeContacto.EVENTO_ASTERISK_DIALSTATUS_CONGESTION: 0,
        }

        # item[0] -> contact_id / item[1] -> ARRAY / item[2]
        for __, array_eventos in listado:
            eventos = set(array_eventos)
            ## Chequea finalizados y no finalizados

            finalizado = False
            for finalizador in finalizadores:
                if finalizador in eventos:
                    finalizado = True
                    break
            if finalizado == False:

                # aca se guarda el evento priorida priorizando siempre a busy
                # Este es el orden de prioridad busy, no answer,failed
                # (congestion, canal no disponible)
                evento_prioridad = 0
                for ev in array_eventos:

                    if ev == EventoDeContacto.EVENTO_ASTERISK_DIALSTATUS_BUSY:
                        evento_prioridad = ev
                        break
                    elif ev == EventoDeContacto.EVENTO_ASTERISK_DIALSTATUS_NOANSWER:
                        evento_prioridad = ev
                    elif ev == EventoDeContacto.EVENTO_ASTERISK_DIALSTATUS_CHANUNAVAIL or\
                    ev == EventoDeContacto.EVENTO_ASTERISK_DIALSTATUS_CONGESTION:
                        if not evento_prioridad == EventoDeContacto.EVENTO_ASTERISK_DIALSTATUS_NOANSWER:
                            evento_prioridad = ev
                if evento_prioridad != 0:
                    counter_por_evento[evento_prioridad] += 1

        return counter_por_evento

    def _obtener_totales_atendidos_por_evento_amd(self, listado):
        """
        Se encarga de obtener los contadores de ciertos eventos(humano,
        contestador)
        fabian decidió no tener en cuenta indefinido (
        EVENTO_ASTERISK_AMD_FAILED)

        :param listado: por cada contacto de la campana me trae un array 
                        con los eventos.
        :return: me retorna un diccionario con los contadores de los 
                 eventos mencionados 
        """
        finalizadores = EventoDeContacto.objects.get_eventos_finalizadores()

        counter_por_evento = {
            EventoDeContacto.EVENTO_ASTERISK_AMD_HUMAN_DETECTED: 0,
            EventoDeContacto.EVENTO_ASTERISK_AMD_MACHINE_DETECTED: 0,
        }

        # item[0] -> contact_id / item[1] -> ARRAY / item[2]
        for _, array_eventos in listado:
            eventos = set(array_eventos)
            ## Chequea finalizados y no finalizados

            finalizado = False
            for finalizador in finalizadores:
                if finalizador in eventos:
                    finalizado = True
                    break

            if finalizado is True:
                for ev in array_eventos:
                    if ev in (EventoDeContacto.EVENTO_ASTERISK_AMD_HUMAN_DETECTED,
                              EventoDeContacto.EVENTO_ASTERISK_AMD_MACHINE_DETECTED):
                        counter_por_evento[ev] += 1

        return counter_por_evento

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

        # porcentaje para no atendidos
        porcentaje_ocupados = 0.0
        porcentaje_no_constestados = 0.0
        porcentaje_canal_no_disponible = 0.0
        porcentaje_congestion = 0.0
        total_ocupados = 0
        total_no_constestados= 0
        total_canal_no_disponible = 0
        total_congestion = 0
        # porcentaje para atendidos
        porcentaje_humanos = 0.0
        porcentaje_contestador = 0.0
        total_humanos = 0
        total_contestador= 0
        if tipo_agregacion is AgregacionDeEventoDeContacto.TIPO_AGREGACION_REPORTE:
            # obtenemos el listado de los eventos
            listado = EventoDeContacto.objects_estadisticas.\
                obtener_eventos_por_contacto(campana)
            # total por cada evento
            counter_por_evento = self._obtener_total_no_atendidos_por_evento(listado)
            # obtenemos el total de ocupado
            total_ocupados = counter_por_evento[EventoDeContacto.EVENTO_ASTERISK_DIALSTATUS_BUSY]
            # obtenemos el total no constestado
            total_no_constestados = counter_por_evento[EventoDeContacto.EVENTO_ASTERISK_DIALSTATUS_NOANSWER]
            # obtenemos el total de canal no disponible
            total_canal_no_disponible = counter_por_evento[EventoDeContacto.EVENTO_ASTERISK_DIALSTATUS_CHANUNAVAIL]
            # obtenemos el total de congestion
            total_congestion = counter_por_evento[EventoDeContacto.EVENTO_ASTERISK_DIALSTATUS_CONGESTION]

            if total_no_atendidos > 0:
                porcentaje_ocupados = (100.0 * float(counter_por_evento[EventoDeContacto.EVENTO_ASTERISK_DIALSTATUS_BUSY]) /
                                       float(total_no_atendidos))
                porcentaje_no_constestados = (100.0 * float(counter_por_evento[EventoDeContacto.EVENTO_ASTERISK_DIALSTATUS_NOANSWER]) /
                                              float(total_no_atendidos))
                porcentaje_canal_no_disponible = (100.0 * float(counter_por_evento[EventoDeContacto.EVENTO_ASTERISK_DIALSTATUS_CHANUNAVAIL]) /
                                              float(total_no_atendidos))
                porcentaje_congestion = (100.0 * float(counter_por_evento[EventoDeContacto.EVENTO_ASTERISK_DIALSTATUS_CONGESTION]) /
                                              float(total_no_atendidos))

            # obtener total por eventos atendidos
            counter_por_evento_atendido = self._obtener_totales_atendidos_por_evento_amd(listado)
            # obtenemos total de atendidos por humanos
            total_humanos = counter_por_evento_atendido[EventoDeContacto.EVENTO_ASTERISK_AMD_HUMAN_DETECTED]
            # obtenemos total de atendidos por contestador
            total_contestador = counter_por_evento_atendido[EventoDeContacto.EVENTO_ASTERISK_AMD_MACHINE_DETECTED]
            if total_atentidos > 0:
                porcentaje_humanos = (100.0 * float(counter_por_evento_atendido[EventoDeContacto.EVENTO_ASTERISK_AMD_HUMAN_DETECTED]) /
                                       float(total_atentidos))
                porcentaje_contestador = (100.0 * float(counter_por_evento_atendido[EventoDeContacto.EVENTO_ASTERISK_AMD_MACHINE_DETECTED]) /
                                              float(total_atentidos))

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
            'total_ocupados': total_ocupados,
            'porcentaje_ocupados': porcentaje_ocupados,
            'total_no_constestados': total_no_constestados,
            'porcentaje_no_constestados': porcentaje_no_constestados,
            'total_canal_no_disponible': total_canal_no_disponible,
            'total_congestion': total_congestion,
            'porcentaje_canal_no_disponible': porcentaje_canal_no_disponible,
            'porcentaje_congestion': porcentaje_congestion,
            'total_humanos': total_humanos,
            'total_contestador': total_contestador,
            'porcentaje_humanos': porcentaje_humanos,
            'porcentaje_contestador': porcentaje_contestador,

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

            # @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
            # Hack fiero para pasar los datos de las duraciones de llamadas
            # al template. Se eliminará con el refactor de este servicio.
            # @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
            estadisticas_de_campana = json.loads(campana.estadisticas)
            datos = estadisticas_de_campana['duracion_de_llamadas']
            estadisticas.update({
                'si_escucharon_todo_el_mensaje':
                    datos['si_escucharon_todo_el_mensaje'],
                'no_escucharon_todo_el_mensaje':
                    datos['no_escucharon_todo_el_mensaje'],
                })
            # @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@

            # Torta: porcentajes de contestados, no contestados y no llamados.
            torta_no_atendidos = pygal.Pie(  # @UndefinedVariable
                                             style=ESTILO_MULTICOLOR)

            torta_no_atendidos.title = "Resultado de no atendidos"
            torta_no_atendidos.add('Ocupados', estadisticas[
                'porcentaje_ocupados'])
            torta_no_atendidos.add('No constestados', estadisticas[
                'porcentaje_no_constestados'])
            torta_no_atendidos.add('Canal no disponible', estadisticas[
                'porcentaje_canal_no_disponible'])
            torta_no_atendidos.add('Congestion', estadisticas[
                'porcentaje_congestion'])

            # Torta: porcentajes de atendidos por humanos y contestadores.
            torta_atendidos = pygal.Pie(  # @UndefinedVariable
                                             style=ESTILO_MULTICOLOR)

            torta_atendidos.title = "Resultado de atendidos"
            torta_atendidos.add('Humanos', estadisticas[
                'porcentaje_humanos'])
            torta_atendidos.add('Contestador', estadisticas[
                'porcentaje_contestador'])


            return {
                'estadisticas': estadisticas,
                'torta_general': torta_general,
                'torta_opcion_x_porcentaje': torta_opcion_x_porcentaje,
                'barra_atendidos_intentos': barra_atendidos_intentos,
                'torta_no_atendidos': torta_no_atendidos,
                'torta_atendidos': torta_atendidos,
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
        return DuracionDeLlamada.objects.obtener_de_campana(campana)

    def _calcular_estadisticas(self, campana, duracion_de_llamadas):
        cursor = connection.cursor()
        sql = """SELECT
        COUNT(duracion_en_segundos) AS si_escucharon_todo,
        (SELECT COUNT(duracion_en_segundos) AS no_escucharon_todo
         FROM fts_web_duraciondellamada
         WHERE campana_id = %(campana_id)s
         AND duracion_en_segundos < %(duracion_de_audio)s)
        FROM fts_web_duraciondellamada
        WHERE campana_id = %(campana_id)s
        AND duracion_en_segundos >= %(duracion_de_audio)s
        """

        params = {'campana_id': campana.id,
                  'duracion_de_audio':
                  self._obtener_duracion_de_audio_en_segundos(campana)}

        with log_timing(logger, "_calcular_estadisticas() tardo %s seg"):
            cursor.execute(sql, params)
            values = cursor.fetchone()

        return json.dumps({
            "duracion_de_llamadas": {
                "si_escucharon_todo_el_mensaje": values[0],
                "no_escucharon_todo_el_mensaje": values[1],
            }
        })

    def _obtener_duracion_de_audio_en_segundos(self, campana):
        # Obtenemos la duración del audio de la campana.
        duracion_de_audio_en_segundos = \
            campana.obtener_duracion_de_audio_en_segundos()
        # Le restamos el porcentaje establecido que diferencia de un mensaje
        # escuchado y un mensaje no escuchado.
        diferencia_duracion_de_audio = \
            settings.FTS_MARGEN_DIFERENCIA_DURACION_LLAMADAS
        duracion_de_audio_en_segundos -= (
            duracion_de_audio_en_segundos * diferencia_duracion_de_audio)

        return duracion_de_audio_en_segundos

    def _guardar_estadisticas(self, campana, estadisticas_calculadas):
        campana.estadisticas = estadisticas_calculadas
        campana.save()

    def generar_estadisticas(self, campana):
        """
        Se encarga de guardar en Campana el cálculo de las estadísticas para
        la duración de las llamadas de la campana.
        """
        # Obtenemos las duraciones de las llamada de la campana.
        duracion_de_llamadas = \
            self._obtener_duracion_de_llamada(campana)

        # Obtenemos el calculo de las estadísticas para la campana.
        estadisticas_calculadas = self._calcular_estadisticas(
            campana, duracion_de_llamadas)

        # Guardamos las estadísticas en la campana.
        self._guardar_estadisticas(campana, estadisticas_calculadas)