# -*- coding: utf-8 -*-
"""
Daemon que busca pendientes y origina los envios.
"""

from __future__ import unicode_literals

from datetime import datetime, timedelta
import os
import random
import time

from django.conf import settings
from fts_daemon.asterisk_ami_http import AmiStatusTracker
from fts_daemon.llamador_contacto import procesar_contacto
from fts_web.models import Campana, EventoDeContacto
import logging as _logging


#
# Import settings & models ^ALLA ARRIBA^ to force setup of Django
#
# Seteamos nombre, sino al ser ejecutado via uWSGI
#  el logger se llamara '__main__'
logger = _logging.getLogger('fts_daemon.poll_daemon')


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
    """Trackea los envios pendientes de UNA campaña"""

    def __init__(self, campana):

        self.campana = campana
        """Campaña siendo trackeada:
        :class:`fts_web.models.Campana`
        """

        self.cache = []
        """Cache de pendientes"""

        # FIXME: usar actuacion!!!
        # self.actuacion = None

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
        pass # nada por ahora

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

    def _populate_cache(self):
        """Busca los pendientes en la BD, y guarda los datos a
        devolver (en las proximas llamadas a `get()`) en cache.

        :raises: NoMasContactosEnCampana: si no hay mas llamados pendientes
        :raises: CampanaNoEnEjecucion: si la campaña ya no esta en ejecucion,
                 porque esta fuera del rango de fechas o de actuaciones
        """
        if not self.campana.verifica_fecha(datetime.now()):
            raise CampanaNoEnEjecucion()

#        self.actuacion = self.campana.obtener_actuacion_actual()
#        if not self.actuacion:
#            logger.info("Cancelando xq no hay actuacion activa para "
#                "campana %s", self.campana.id)
#            raise CampanaNoEnEjecucion()

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

        # Fecha actual local.
        hoy_ahora = datetime.now()

        # Esto quiza no haga falta, porque en teoria
        # el siguiente control de actuacion detectara el
        # cambio de dia, igual hacemos este re-control
        if not self.campana.verifica_fecha(hoy_ahora):
            raise CampanaNoEnEjecucion()

        if self.limite_alcanzado():
            msg = ("Hay {0} llamadas en curso (aprox), y la campana "
                "tiene un limite de {1}").format(
                    self._llamadas_en_curso_aprox,
                    self.campana.cantidad_canales)
            raise LimiteDeCanalesAlcanzadoError(msg)

        #if not self.actuacion.verifica_actuacion(hoy_ahora):
        #    raise CampanaNoEnEjecucion()

        # Valida que la campana esté en estado valido
        if not Campana.objects.verifica_estado_activa(self.campana.pk):
            raise CampanaNoEnEjecucion()

        if not self.cache:
            self._populate_cache()  # -> NoMasContactosEnCampana

        self._llamadas_en_curso_aprox += 1
        return self.cache.pop(0)


class BanManager(object):
    """Gestiona baneo de campañas"""

    def __init__(self):
        self.campanas_baneadas = {}
        """Diccionario que mapea campana (key) al datetime indicando el
        momento hasta el cual la campaña esta baneada"""

    def get_timedelta_baneo(self):
        """Devuelve tiempo por default de baneo"""
        return timedelta(minutes=1)

    def banear_campana(self, campana):
        """Banea una campana"""
        self.campanas_baneadas[campana] = datetime.now() + \
            self.get_timedelta_baneo()

    def esta_baneada(self, campana):
        """Devuelve booleano indicando si la campana esta baneada
        """
        try:
            baneada_hasta = self.campanas_baneadas[campana]
        except KeyError:
            # Campaña no existe, asi q' no esta baneada...
            return False

        # Existe! Chequeamos si todavia está vigente
        if datetime.now() < baneada_hasta:
            return True
        else:
            del self.campanas_baneadas[campana]
            return False


# FIXME: renombra a RoundRobinScheduler
class RoundRobinTracker(object):
    """Con la ayuda de CampanaTracker, devuelve contactos a realizar
    de a una campaña por vez, teniendo en cuenta los límites configurados
    en las campañas.
    """

    def __init__(self):
        self.trackers_campana = {}
        """Diccionario con los trackers de las campañas siendo procesadas.

        :key: :class:`fts_web.models.Campana`
        :value: :class:`.CampanaTracker`
        """

        self.ami_status_tracker = AmiStatusTracker()
        """Status tracker via HTTP AMI"""

        self.ban_manager = BanManager()
        """Administrador de baneos"""

        # Quiza esto deberia estar en `self.trackers_campana`
        self._ultimo_refresco_trackers = datetime.now() - timedelta(days=30)
        """Ultima vez q' se consulto la BD, para refrescar los
        trackers. Es usado por necesita_refrescar_trackers() y
        refrescar_trackers()
        """

        # Quiza esto deberia estar en `self.ami_status_tracker`
        self._ultimo_refresco_ami_status = datetime.now() - timedelta(days=30)
        """Ultima vez q' se ejecuto *ŝtatus* via AMI HTTP."""

        self.max_iterations = None

    def necesita_refrescar_trackers(self):
        """Devuleve booleano, indicando si debe o no consultarse a
        la base de datos. Este metodo es ejecutado en cada ROUND,
        por lo tanto, debe ser rapido.

        Si devuelve 'True', se consultara la BD para actualizar
        la lista de campanas. Sino, se seguira utilizando la
        lista cacheada.

        En una futura implementación, además de utilizar un "timeout",
        podriamos chequear alguna variable que sea seteada
        asincronamente (ej: usando Redis), o podriamos conocer cuanto
        falta para que una campana se active (por fecha de la
        campaña o Actuacion).
        """
        # Quizá habria q' chequear más seguido si el server no
        # está haciendo nada, pero más espaciado si hay
        # llamadas en curso, no?
        delta = datetime.now() - self._ultimo_refresco_trackers
        if delta.days > 0 or delta.seconds > 10:
            return True
        return False

    def _obtener_campanas_en_ejecucion(self):
        """Devuelve campañas en ejecucion. Las busca en la BD"""
        return Campana.objects.obtener_ejecucion()

    def refrescar_trackers(self):
        """Refresca la lista de trackers de campañas (self.trackers_campana),
        que incluye buscar en BD las campañas en ejecucion.

        Se crean instancias de CampanaTracker SOLO para las nuevas campañas.
        Las instancias de CampanaTracker para campañas que ya están siendo
        traqueadas con mantenidas. Las instancias de CampanaTracker de campañas
        que ya no son más trackeadas, son eliminadas.

        :raises: NoHayCampanaEnEjecucion
        """
        logger.debug("refrescar_trackers(): Iniciando...")
        self._ultimo_refresco_trackers = datetime.now()
        old_trackers = dict(self.trackers_campana)
        new_trackers = {}
        for campana in self._obtener_campanas_en_ejecucion():

            if self.ban_manager.esta_baneada(campana):
                logger.debug("La campana %s esta baneada", campana.id)
                continue

            if campana in old_trackers:
                # Ya existia de antes, la mantenemos
                new_trackers[campana] = old_trackers[campana]
                del old_trackers[campana]
            else:
                # Es nueva
                logger.debug("refrescar_trackers(): nueva campana: %s",
                    campana.id)
                new_trackers[campana] = CampanaTracker(campana)

        self.trackers_campana = new_trackers

        # Logueamos campanas q' no van mas...
        for campana in old_trackers:
            logger.info("refrescar_trackers(): quitando campana %s",
                campana.id)

        # Luego de procesar y loguear todo, si vemos q' no hay campanas
        # ejecucion, lanzamos excepcion
        if not self.trackers_campana:
            # No se encontraron campanas en ejecucion
            raise NoHayCampanaEnEjecucion()

    def necesita_refrescar_channel_status(self):
        """Devuelve booleano indicando si debe y es conveniente refrescar
        el status de los channels de Asterisk"""

        if not self.trackers_campana:
            logger.debug("necesita_refrescar_channel_status(): no actualizamos"
                " porque no hay self.trackers_campana")
            return False

        al_limite = [tracker.limite_alcanzado()
            for tracker in self.trackers_campana.values()]

        if True not in al_limite:
            logger.debug("necesita_refrescar_channel_status(): no actualizamos"
                " porque no se alcanzo el limite en ninguna campaña")
            return False

        if all(al_limite):
            logger.debug("necesita_refrescar_channel_status(): todas las "
                "campañas estan al limite")

        delta = datetime.now() - self._ultimo_refresco_ami_status
        # No hacemos más de 1 consulta cada 3 segundos
        if delta.days == 0 and delta.seconds < 3:
            logger.debug("necesita_refrescar_channel_status(): no actualizamos"
                " porque la ultima actualizacion fue recientemente")
            return False

        logger.debug("necesita_refrescar_channel_status(): True")
        return True

    def refrescar_channel_status(self):
        """Refresca `llamadas_en_curso_aprox` de `self.trackers_campana`,
        en caso que sea necesario y conveniente.

        En caso de error, no actualiza ningun valor.
        """
        # Antes q' nada, actualizamos 'ultimo refresco'
        self._ultimo_refresco_ami_status = datetime.now()

        logger.info("Actualizando status via AMI HTTP")
        try:
            status = self.ami_status_tracker.get_status_por_campana()
        except:
            logger.exception("Error detectado al ejecutar "
                "ami_status_tracker.get_status_por_campana(). Los statuses "
                "no seran actualizados")
            return

        #======================================================================
        # Actualizamos estructuras...
        #======================================================================

        # Dict con campañas trackeadas, indexadas por 'ID'
        campana_by_id = dict([(c.id, c) for c in self.trackers_campana])

        for campana_id, info_de_llamadas in status.iteritems():
            # info_de_llamadas => [contacto_id, numero, campana_id]
            if campana_id in campana_by_id:
                campana = campana_by_id[campana_id]
                tracker = self.trackers_campana[campana]
                tracker.llamadas_en_curso_aprox = len(info_de_llamadas)
                del campana_by_id[campana_id]
            else:
                logger.info("refrescar_channel_status(): "
                    "Ignorando datos de campana %s (%s llamadas en curso)",
                    campana.id, len(info_de_llamadas))

        # En este punto, campana_by_id tiene las campañas cuyos datos
        #  no fueron refrescados...
        for campana in campana_by_id.values():
            # FIXME: esto que hacemos aca, no es algo peligroso? Y si habia
            # en ejecucion!? Quizá deberiamos, además de este control, llevar
            # control de la cantidad de llamadas generadas por minuto
            logger.info("refrescar_channel_status(): no se recibieron "
                "datos para la campana %s... Suponemos que no hay "
                "llamadas en curso para dicha campana", campana.id)
            tracker = self.trackers_campana[campana]
            tracker.llamadas_en_curso_aprox = 0

    def onNoHayCampanaEnEjecucion(self):
        """Ejecutado por generator() cuando se detecta
        NoHayCampanaEnEjecucion.
        """
        logger.debug("No hay campanas en ejecucion.")

    def onCampanaNoEnEjecucion(self, campana):
        """Ejecutado por generator() cuando se detecta
        CampanaNoEnEjecucion. Esto implica que la campana que se
        estaba por ejecutar, NO debio tenerse en cuenta.

        La implementación por default banea a la campana, y la
        elimina de `self.trackers_campana`
        """
        self.ban_manager.banear_campana(campana)
        logger.debug("onCampanaNoEnEjecucion: %s", campana.id)
        try:
            del self.trackers_campana[campana]
        except KeyError:
            pass

    def onNoMasContactosEnCampana(self, campana):
        """Ejecutado por generator() cuando se detecta
        NoMasContactosEnCampana. Esto implica que la campana que se
        estaba teniendo en cuenta en realidad no posee contactos
        a procesar

        La implementación por default banea a la campana, y la
        elimina de `self.trackers_campana`
        """
        logger.debug("onNoMasContactosEnCampana() para la campana %s.",
            campana.id)
        self.ban_manager.banear_campana(campana)
        try:
            del self.trackers_campana[campana]
        except KeyError:
            pass

    def onLimiteDeCanalesAlcanzadoError(self, campana):
        """Ejecutado por generator() cuando se detecta
        LimiteDeCanalesAlcanzadoError.

        Esto NO deberia suceder, ya que las campañas que están
        al limite no son procesadas.
        """
        logger.debug("onLimiteDeCanalesAlcanzadoError() para la campana %s",
            campana.id)

    def onNoSeDevolvioContactoEnRoundActual(self):
        """Ejecutado por generator() cuando se corrió el loop, pero no se
        devolvio ningun contacto.

        Esto no deberia suceder, pero hay algunos corner cases, por ejemplo,
        la actuacion o la campaña se vencieron justo mientras se estaban
        por procesar.
        """

    def sleep(self, segundos):
        """Wrapper de time.sleep()."""
        time.sleep(segundos)

    def _todas_las_campanas_al_limite(self):
        """Chequea trackers y devuelve True si TODAS las campañas
        en curso estan al limite"""
        al_limite = [tracker.limite_alcanzado()
            for tracker in self.trackers_campana.values()]

        if al_limite and all(al_limite):
            return True
        return False

    def generator(self):
        """Devuelve los datos de contacto a contactar, de a una
        campaña por vez.

        :returns: (campana, contacto_id, telefono)
        """

        iter_num = 0
        while True:

            if self.max_iterations is not None:
                iter_num += 1
                if iter_num >= self.max_iterations:
                    raise Exception("Se supero la cantidad maxima de "
                        "iteraciones: {0}".format(self.max_iterations))

            #==================================================================
            # Actualizamos trackers de campaña
            #==================================================================

            if self.necesita_refrescar_trackers():
                try:
                    self.refrescar_trackers()
                except NoHayCampanaEnEjecucion:
                    self.onNoHayCampanaEnEjecucion()

            #==================================================================
            # Si no hay campañas, espseramos y reiniciamos
            #==================================================================

            if not bool(self.trackers_campana):
                # No hay trabajo! Esperamos y hacemos `continue`
                # +------------------------------------------------------------
                # | Los eventos que deberian despertar este 'sleep' son:
                # | 1. campaña des-pausada
                # | 2. campaña entra en curso (por fecha u hora de actuacion)
                # | 3. campaña creada
                # +------------------------------------------------------------
                logger.debug("No hay trabajo. Esperamos %s segs. y luego "
                    "hacemos continue (reiniciamos ROUND)",
                    settings.FTS_DAEMON_SLEEP_SIN_TRABAJO)
                self.sleep(settings.FTS_DAEMON_SLEEP_SIN_TRABAJO)

                # No importa q' no se refresque el status via ami, total,
                #    no hay trabajo!
                continue

            #==================================================================
            # Refrescamos status de conexiones
            #==================================================================

            if self.necesita_refrescar_channel_status():
                self.refrescar_channel_status()

            # Si TODAS las campañas han llegado al límite, no tiene sentido
            # hacer un busy wait... mejor esperamos
            # +----------------------------------------------------------------
            # | Los eventos que deberian despertar este 'sleep' son:
            # | 1. se ha finalizado la llamada de cualquiera de las
            # |    campañas q' habian llegado al limite
            # +----------------------------------------------------------------

            if self._todas_las_campanas_al_limite():
                logger.debug("Todas las campañas han llegado al límite. "
                    "Esperamos %s segs. y reiniciamos round",
                    settings.FTS_DAEMON_SLEEP_LIMITE_DE_CANALES)
                self.sleep(settings.FTS_DAEMON_SLEEP_LIMITE_DE_CANALES)
                continue

            ##
            ## Procesamos...
            ##

            loop__campanas_procesadas = 0

            # Trabajamos en copia, por si hace falta modificarse
            dict_copy = dict(self.trackers_campana)

            for campana, tracker in dict_copy.iteritems():
                # Si la campana esta al limite, la ignoramos
                if tracker.limite_alcanzado():
                    logger.debug("Ignorando campana %s porque esta al limite",
                        campana.id)
                    continue

                tracker.reset_loop_flags()
                try:
                    yield tracker.next()
                    loop__campanas_procesadas += 1
                except CampanaNoEnEjecucion:
                    # CORNER CASE!
                    self.onCampanaNoEnEjecucion(campana)
                except NoMasContactosEnCampana:
                    # Esta excepcion es generada cuando la campaña esta
                    # en curso (el estado), pero ya no tiene pendientes
                    # FIXME: aca habria q' marcar la campana como finalizada?
                    # El tema es que puede haber llamadas en curso, pero esto
                    # no deberia ser problema...
                    self.onNoMasContactosEnCampana(campana)
                except LimiteDeCanalesAlcanzadoError:
                    # ESTO NO DEBERIA SUCEDER! No debio ejecutarse
                    # tracker.next() si la campaña estaba al limite
                    logger.exception("Se detecto "
                        "LimiteDeCanalesAlcanzadoError al procesar la campana "
                        "{0}, pero nunca debio intentarse obtener un contacto "
                        "de esta campana si estaba al limite".format(
                            campana.id))
                    self.onLimiteDeCanalesAlcanzadoError(campana)

            # CORNER CASE: solo podria pasar si justo, mientras se
            # procesaban las campañas, cambio la hora y/o el dia
            if loop__campanas_procesadas == 0:
                logger.warn("No se ha devuelto ningun contacto en el "
                    "ROUND actual")
                self.onNoSeDevolvioContactoEnRoundActual()


class Llamador(object):
    """Utiliza RoundRobinTracker para obtener números a contactar,
    y realiza los llamados.
    """

    def __init__(self):
        self.rr_tracker = RoundRobinTracker()

    def run(self, max_loops=0):
        """Inicia el llamador"""
        current_loop = 1
        for campana, id_contacto, numero in self.rr_tracker.generator():
            logger.debug("Llamador.run(): campana: %s - id_contacto: %s"
                " - numero: %s", campana, id_contacto, numero)

            procesar_contacto(campana, id_contacto, numero)

            current_loop += 1
            if max_loops > 0 and current_loop > max_loops:
                logger.info("Llamador.run(): max_loops alcanzado. Exit!")
                return


def main(max_loop=0):
    logger.info("Iniciando loop: obteniendo campanas activas...")
    FTS_MAX_LOOPS = int(os.environ.get("FTS_MAX_LOOPS", max_loop))
    FTS_INITIAL_WAIT = int(os.environ.get("FTS_INITIAL_WAIT", "0"))
    if FTS_INITIAL_WAIT > 0:
        logger.info("Iniciando espera inicial de %s segs...", FTS_INITIAL_WAIT)
        time.sleep(FTS_INITIAL_WAIT)
        logger.info("Espera inicial finalizada")
    Llamador().run(max_loops=FTS_MAX_LOOPS)


if __name__ == '__main__':
    main()
