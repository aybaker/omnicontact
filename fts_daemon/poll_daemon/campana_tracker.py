# -*- coding: utf-8 -*-
"""

"""

from __future__ import unicode_literals

from datetime import datetime
import random

from fts_web.models import Campana, EventoDeContacto
import logging as _logging


# Seteamos nombre, sino al ser ejecutado via uWSGI
#  el logger se llamara '__main__'
logger = _logging.getLogger(__name__)


class CampanaNoEnEjecucion(Exception):
    """Marca que la campaña en cuestion no está "en ejecucion",
    ya sea por el estado (ej: pausada), no esta en rango de fecha de campaña,
    o en rango de horas de actuaciones
    """


class NoMasContactosEnCampana(Exception):
    """No se encontraron contactos por procesar para la campaña.
    """


class NoHayCampanaEnEjecucion(Exception):
    """No se encontraron campanas en ejecucion.
    """


class LimiteDeCanalesAlcanzadoError(Exception):
    """Se alcanzó el límite máximo de llamadas concurrentes que pude
    poseer una campana.
    """


class CampanaTracker(object):
    """Trackea los envios pendientes de UNA campaña. La vida de las
    instancias estan la actuación en curso.
    """

    def __init__(self, campana):

        self.campana = campana
        """Campaña siendo trackeada: :class:`fts_web.models.Campana`
        """

        self.cache = []
        """Cache de pendientes"""

        self.actuacion = campana.obtener_actuacion_actual()
        """Actuacion de la campana, para este momento.
        :class:`fts_web.models.Actuacion`.

        CORNER CASE: puede q' ya no haya actuacion actual, si justo
        en los milisegundos anteriores se pasó la hora especificada
        por 'hora_hasta'. En estos casos, ``self.actuacion`` podria
        ser None, o fuera de rango (o sea, no en curso).
        """

        self.fetch_min = 20
        """Cantidad minima a buscar en BD para cachear"""

        self.fetch_max = 100
        """Cantidad maxima a buscar en BD para cachear"""

        self._llamadas_en_curso_aprox = 0
        """Lleva un contador de las llamadas en curso aproximadas
        para esta campaña. Este valor es refrescado cada tanto con los
        datos devueltos por AsteriskHttpClient() (es ese momento no será
        aproximado, sino que será el valor cierto). Luego, con cada originate,
        incrementamos el contador en 1... lo que lo hace aproximado es que
        registramos las llamadas nuevas iniciadas, pero NO descontamos
        las llamadas finalizadas.

        ORIGINATE ASYNC: AsteriskHttpClient() devuelve informacion de las
        llamadas que todavia no fueron contestadas (en estado RINGING), por
        lo tanto, por lo tanto, nos da una visión bastante cierta de la
        cantidad de canales ocupados.
        """

    def limite_alcanzado(self):
        """Devuelve booleano si se ha alcanzado (o superado) el limite de
        canales para la campaña siendo trackeada.

        Ya que nos basamos en el valor de `_llamadas_en_curso_aprox`, pueden
        reportarse "falsos positivos", o sea, que se indique que el limite
        se ha alcanzado, pero no sea cierto.
        """
        return self._llamadas_en_curso_aprox >= self.campana.cantidad_canales

    def reset_loop_flags(self):
        """Resetea todas las variables y banderas de ROUND, o sea, las
        variables y banderas que son reseteadas antes de iniciar el ROUND
        """
        pass  # nada por ahora

    @property
    def llamadas_en_curso_aprox(self):
        """Cantidad aproximada de llamadas en curso"""
        return self._llamadas_en_curso_aprox

    @llamadas_en_curso_aprox.setter
    def llamadas_en_curso_aprox(self, value):
        logger.debug("Actualizando llamadas_en_curso_aprox, de %s a %s",
            self._llamadas_en_curso_aprox, value)
        assert type(value) == int
        self._llamadas_en_curso_aprox = value

    def _get_random_fetch(self):
        return random.randint(self.fetch_min, self.fetch_max)

    def _obtener_pendientes(self):
        """Devuelve información de contactos pendientes de contactar"""
        return EventoDeContacto.objects_gestion_llamadas.\
            obtener_pendientes(self.campana.id, limit=self._get_random_fetch())

    def _obtener_datos_de_contactos(self, contactos_values):
        return EventoDeContacto.objects_gestion_llamadas.\
            obtener_datos_de_contactos([tmp[1] for tmp in contactos_values])

    def _verifica_fecha_y_hora(self):
        """Verifica q' fecha con datos de campaña, y hora con datos
        de la actuacion.

        :raises: CampanaNoEnEjecucion
        """
        hoy_ahora = datetime.now()
        if not self.campana.verifica_fecha(hoy_ahora):
            raise CampanaNoEnEjecucion()

        if not self.actuacion:
            logger.info("Cancelando xq no hay actuacion activa para "
                "campana %s", self.campana.id)
            raise CampanaNoEnEjecucion()

        if not self.actuacion.verifica_actuacion(hoy_ahora):
            logger.info("Cancelando xq no hay actuacion activa para "
                "campana %s", self.campana.id)
            raise CampanaNoEnEjecucion()

    def _populate_cache(self):
        """Busca los pendientes en la BD, y guarda los datos a
        devolver (en las proximas llamadas a `get()`) en cache.

        :raises: NoMasContactosEnCampana: si no hay mas llamados pendientes
        :raises: CampanaNoEnEjecucion: si la campaña ya no esta en ejecucion,
                 porque esta fuera del rango de fechas o de actuaciones
        """
        self._verifica_fecha_y_hora()

        contactos_values = self._obtener_pendientes()

        if not contactos_values:
            raise NoMasContactosEnCampana()

        id_contacto_y_telefono = self._obtener_datos_de_contactos(
            contactos_values)

        self.cache = [(self.campana, contacto_id, telefono)
            for contacto_id, telefono in id_contacto_y_telefono]

    def next(self):
        """Devuelve los datos de datos de contacto a contactar,
        para la campaña asociada a este tracker. Internamente, se encarga
        de obtener el generador, y obtener un dato.

        :returns: (campana, contacto_id, telefono)

        :raises: CampanaNoEnEjecucion
        :raises: NoMasContactosEnCampana
        :raises: LimiteDeCanalesAlcanzadoError
        """
        self._verifica_fecha_y_hora()

        if self.limite_alcanzado():
            msg = ("Hay {0} llamadas en curso (aprox), y la campana "
                "tiene un limite de {1}").format(
                    self._llamadas_en_curso_aprox,
                    self.campana.cantidad_canales)
            raise LimiteDeCanalesAlcanzadoError(msg)

        # Valida que la campana esté en estado valido
        if not Campana.objects.verifica_estado_activa(self.campana.pk):
            raise CampanaNoEnEjecucion()

        if not self.cache:
            self._populate_cache()  # -> NoMasContactosEnCampana

        self._llamadas_en_curso_aprox += 1
        return self.cache.pop(0)
