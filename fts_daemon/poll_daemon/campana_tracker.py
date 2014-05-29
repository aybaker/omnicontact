# -*- coding: utf-8 -*-
"""

"""

from __future__ import unicode_literals

from datetime import datetime
import pprint
import random

from fts_daemon.models import EventoDeContacto
from fts_web.models import Campana
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
    """No se encontraron contactos por procesar para la campaña,
    y por lo tanto se ha finalizado el procesamineto de la campaña
    """


class TodosLosContactosPendientesEstanEnCursoError(Exception):
    """Hay contactos con intentos por realizar, pero todos corresponden
    a contactos que en este momento estan con llamadas en curso.

    Esta es una situacion muy especial, que puede darse solamente cuando
    se está finalizando el ultimo intento de una campaña.
    """


class LimiteDeCanalesAlcanzadoError(Exception):
    """Se alcanzó el límite máximo de llamadas concurrentes que pude
    poseer una campana.
    """


class CampanaTracker(object):
    """Trackea los envios pendientes de UNA campaña. Tambien trackea
    (de manera aproximada) las llamadas en curso para dicha campaña.

    Una instancia de CampanaTracker puede estar ACTIVA, cuando se trata
    de una campaña 'en ejecucion'. En este caso, se mantiene el cache y
    la actuacion asociada a la campaña.

    Cuando la instancia NO esta ACTIVA, la actuacion y cache son eliminados,
    hasta que se vuelva a reactivar.
    """

    def __init__(self, campana):

        self.campana = campana
        """Campaña siendo trackeada: :class:`fts_web.models.Campana`
        """

        self._activa = True

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

        self.fetch_min = self.campana.cantidad_canales * 2
        """Cantidad minima a buscar en BD para cachear"""

        self.fetch_max = self.campana.cantidad_canales * 5
        """Cantidad maxima a buscar en BD para cachear"""

        self._contactos_en_curso = []
        """Lista con id de contactos con llamadas en curso.

        Este valor es refrescado cada tanto con los
        datos devueltos por AsteriskHttpClient() (es ese momento no será
        aproximado, sino que será el valor cierto). Luego, con cada originate,
        agregamos el contacto devuelto. Lo que lo hace aproximado es que
        registramos las llamadas nuevas iniciadas, pero NO eliminamos
        las llamadas finalizadas.

        ORIGINATE ASYNC: AsteriskHttpClient() devuelve informacion de las
        llamadas que todavia no fueron contestadas (en estado RINGING), por
        lo tanto, nos da una visión bastante cierta de la cantidad de
        canales ocupados.
        """

        if self.fetch_min < 20:
            self.fetch_min = 20

        if self.fetch_max < 100:
            self.fetch_max = 100

    @property
    def activa(self):
        return self._activa

    def desactivar(self):
        """Elimina temporales y demas cosas, utilizado para no guardar
        datos que no serán usados, cuando la campaña siendo trackeada
        ya no está en curso.

        Para volver a utilizar una instancia de, utilizar `update()`.
        """
        self._activa = False
        self.cache = None
        self.actuacion = None

    def update_campana(self, campana):
        """Actualiza la instancia de campana"""
        assert self.campana.id == campana.id
        self.campana = campana

    def reactivar_si_corresponde(self, campana):
        """Actualiza la instancia de campana, y reactiva
        si no esta activa."""
        assert self.campana.id == campana.id
        if self._activa:
            # Si ya esta activa, solo actualizamos `campana`
            self.campana = campana
        else:
            # Si NO esta activa, reactivamos...
            self.reactivar(campana)

    def reactivar(self, campana):
        """Setea el estado interno para poder volver a utilizar una
        instancia, previamente 'desactivada', o sea, a la que previamente
        se llamo el `desactivar()`.

        Tambien actualiza la campana pasada por parametro.
        """
        assert self.campana.id == campana.id
        self._activa = True
        self.campana = campana
        self.cache = []
        self.actuacion = campana.obtener_actuacion_actual()

    # TODO: renombrar a "limite_de_canales_alcanzado" o algo asi
    def limite_alcanzado(self):
        """Devuelve booleano si se ha alcanzado (o superado) el limite de
        canales para la campaña siendo trackeada.

        Ya que nos basamos en el valor de `_contactos_en_curso`, pueden
        reportarse "falsos positivos", o sea, que se indique que el limite
        se ha alcanzado, pero no sea cierto.
        """
        en_curso = len(self._contactos_en_curso)
        if en_curso > self.campana.cantidad_canales:
            # FIXME: buscar la forma de testear que esto se detecta y reporta
            logger.error("limite_alcanzado(): se detectaron %s llamadas en "
                "curso para la campana %s, cuando la cantidad de canales "
                "configurado es %s. Dump de '_contactos_en_curso':\n"
                "%s", en_curso, self.campana.id, self.campana.cantidad_canales,
                pprint.pformat(self._contactos_en_curso))

        return en_curso >= self.campana.cantidad_canales

    @property
    def llamadas_en_curso_aprox(self):
        """Cantidad aproximada de llamadas en curso"""
        return len(self._contactos_en_curso)

    @property
    def contactos_en_curso(self):
        """Contactos con llamadas en curso en este momento"""
        return list(self._contactos_en_curso)

    @contactos_en_curso.setter
    def contactos_en_curso(self, lista_contactos_en_curso):
        """Contactos con llamadas en curso en este momento"""
        logger.debug("Actualizando contactos_en_curso, de %s a %s",
            len(self._contactos_en_curso), len(lista_contactos_en_curso))
        items_are_numbers = [type(value) in [int, long]
            for value in lista_contactos_en_curso]
        assert all(items_are_numbers), "Algun elemento de " + \
            "lista_contactos_en_curso no es int o long"
        self._contactos_en_curso = list(lista_contactos_en_curso)

    def _get_random_fetch(self):
        return random.randint(self.fetch_min, self.fetch_max)

    def _obtener_pendientes(self):
        """Devuelve información de contactos pendientes de contactar.
        Puede devolver contactos que actualmente estan siendo
        contactados."""
        limit = self._get_random_fetch()
        return EventoDeContacto.objects_gestion_llamadas.\
            obtener_pendientes(self.campana.id, limit=limit)

    def _obtener_pendientes_sin_en_curso(self):
        """Devuelve información de contactos pendientes de contactar,
        EXCEPTUANDO contactos con llamadas en curso. Por lo tanto,
        es seguro contactar a los contactos devueltos por este metodo"""
        limit = self._get_random_fetch()
        return EventoDeContacto.objects_gestion_llamadas.\
            obtener_pendientes_no_en_curso(self.campana.id, limit=limit,
                contacto_ids_en_curso=list(self._contactos_en_curso))

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
        :raises: TodosLosContactosPendientesEstanEnCursoError: si hay
                 contactos pendientes, pero todos esos contactos estan
                 en curso actualmente. Esto sólo se deberia dar cuando se
                 estan devolviendo contactos para el ultimo intento de contacto
                 de la campaña.
        """
        self._verifica_fecha_y_hora()

        #
        # Nota general:
        #
        #  1. `_contactos_en_curso` nunca sera mayor q' cant. de canales
        #  2. la BD es > cant. canales
        #
        # Por lo tanto, si `_obtener_pendientes_sin_en_curso()` no devuelve
        #  datos, es porque:
        #      a) no hay mas pendientes (ya se finalizó la campaña)
        #      b) sí hay mas pendientes (pero todos estan en curso)
        #
        # Si sucede (a): hay que lanzar
        #                     `NoMasContactosEnCampana`
        # Si sucede (b): hay que lanzar
        #                     `TodosLosContactosPendientesEstanEnCursoError`
        #

        if self._contactos_en_curso:
            # Tenemos info de llamadas en curso... Usamos esa info para
            # excluir dichos contactos en la busqueda de pendientes
            contactos_sin_en_curso_values = \
                self._obtener_pendientes_sin_en_curso()

            if not contactos_sin_en_curso_values:
                contactos_values = self._obtener_pendientes()
                # ¿Es situacion (a)?
                if not contactos_values:
                    raise NoMasContactosEnCampana()

                # Si llegamos aca, es porque se trata de (b), y entonces
                # `contactos_values` tiene datos
                raise TodosLosContactosPendientesEstanEnCursoError()

            # Si llegamos aca, es porque `contactos_sin_en_curso_values`
            # tiene contactos. Usamos esos valores!
            contactos_values = contactos_sin_en_curso_values

        else:
            # No hay info de contactos en curso
            contactos_values = self._obtener_pendientes()

            if not contactos_values:
                raise NoMasContactosEnCampana()

        # ATENCION: `contactos_values` estan ordenados por cant. de intentos,
        #   asi que cualquier procesamiento que se haga, debe hacerse
        #   teniendo en cuenta el orden definido en dicha lista

        # Si llegamos aca, es porque en `contactos_values` estan
        # los datos a devolver

        # lista de `(id_contacto, telefono)`
        id_contacto_y_telefono = self._obtener_datos_de_contactos(
            contactos_values)
        id_contacto_y_telefono_dict = dict(id_contacto_y_telefono)

        self.cache = [(
            self.campana,
            id_contacto,
            id_contacto_y_telefono_dict[id_contacto],
            intento
        ) for intento, id_contacto in contactos_values]

    def next(self):
        """Devuelve los datos de datos de contacto a contactar,
        para la campaña asociada a este tracker. Internamente, se encarga
        de obtener el generador, y obtener un dato.

        :returns: (campana, contacto_id, telefono, intentos) - En particular,
                  intentos es la cantidad de intentos ya realizados, asi que
                  sera >= a 0, y deberia ser siempre < a la cantidad maxima
                  de intentos configurados en la campaña.

        :raises: CampanaNoEnEjecucion
        :raises: NoMasContactosEnCampana
        :raises: LimiteDeCanalesAlcanzadoError
        :raises: TodosLosContactosPendientesEstanEnCursoError
        """
        self._verifica_fecha_y_hora()

        if self.limite_alcanzado():
            msg = ("Hay {0} llamadas en curso (aprox), y la campana "
                "tiene un limite de {1}").format(
                    self.llamadas_en_curso_aprox,
                    self.campana.cantidad_canales)
            raise LimiteDeCanalesAlcanzadoError(msg)

        # Valida que la campana esté en estado valido
        if not Campana.objects.verifica_estado_activa(self.campana.pk):
            raise CampanaNoEnEjecucion()

        if not self.cache:
            self._populate_cache()
            #         \-> NoMasContactosEnCampana
            #         \-> TodosLosContactosPendientesEstanEnCursoError

        ret_campana, ret_contacto_id, ret_telefono, ret_intentos = \
            self.cache.pop(0)

        # self._llamadas_en_curso_aprox += 1
        self._contactos_en_curso.append(ret_contacto_id)

        return ret_campana, ret_contacto_id, ret_telefono, ret_intentos
