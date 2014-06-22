# -*- coding: utf-8 -*-
"""

"""

from __future__ import unicode_literals

import time

from django.conf import settings
from fts_daemon import llamador_contacto
from fts_daemon.poll_daemon.call_status import CampanaCallStatus, \
    AsteriskCallStatus
from fts_daemon.poll_daemon.campana_tracker import CampanaNoEnEjecucion, \
    NoMasContactosEnCampana, LimiteDeCanalesAlcanzadoError, \
    TodosLosContactosPendientesEstanEnCursoError
from fts_daemon.poll_daemon.originate_throttler import OriginateThrottler
from fts_daemon.poll_daemon.statistics import StatisticsService
from fts_web.models import Campana
import logging as _logging


logger = _logging.getLogger(__name__)

BANEO_NO_MAS_CONTACTOS = "BANEO_NO_MAS_CONTACTOS"
"""Cuando se detecta que una campaña no posee mas contactos
para procesar, se la banea con esta 'razon'"""

BANEO_TODOS_LOS_PENDIENTES_EN_CURSO = "BANEO_TLPEN"
"""Cuando la campaña posee contactos pendientes, pero
todos estos contactos ya están en curso, se las banea
con esta 'razon'"""

BANEO_CAMPANA_FINALIZADA = "BANEO_CAMPANA_FINALIZADA"
"""Luego q' la campaña es baneada con `BANEO_NO_MAS_CONTACTOS`,
la campaña es finalizada. Para evitar que se siga intentando
finalizar, el baneo es cambiado a BANEO_CAMPANA_FINALIZADA"""


class CantidadMaximaDeIteracionesSuperada(Exception):
    pass


def finalizar_campana(campana_id):
    """Finaliza una campaña"""
    campana = Campana.objects.get(pk=campana_id)

    if campana.estado != Campana.ESTADO_ACTIVA:
        logger.info("finalizar_campana(): No finalizaremos campana "
            "%s porque su estado no es ESTADO_ACTIVA", campana.id)
        return

    # LIMITE = settings.FTS_MARGEN_FINALIZACION_CAMPANA
    logger.info("finalizar_campana(): finalizando campana %s", campana.id)

    campana.finalizar()


class ContinueOnOuterWhile(Exception):
    """Excepcion utilizada para romper un bucle"""
    pass


# FIXME: renombra a RoundRobinScheduler
class RoundRobinTracker(object):
    """Con la ayuda de CampanaTracker, devuelve contactos a realizar
    de a una campaña por vez, teniendo en cuenta los límites configurados
    en las campañas.
    """

    def __init__(self):
        """Crea instancia de RoundRobinTracker"""

        self._originate_throttler = OriginateThrottler()
        """Administrador de limites de originates por segundo"""

        self._campana_call_status = CampanaCallStatus()

        self._asterisk_call_status = AsteriskCallStatus(
            self._campana_call_status)

        self._finalizador_de_campanas = finalizar_campana

        self._statistics_service = StatisticsService()

        self.max_iterations = None
        """Cantidad de interaciones maxima que debe realizar ``generator()``.
        Si vale ``None``, no se realiza ningun control.
        Sino, al alcanzar esa cantidad de iteraciones, generator() hace
        return"""

    @property
    def originate_throttler(self):
        return self._originate_throttler

    def publish_statistics(self):
        """Publica las estadisticas, si corresponde"""
        if not self._statistics_service.shoud_update():
            # FIXME: cambiar a logger.debug()
            logger.info("publish_statistics(): no hace falta. Ignorando.")
            return

        logger.debug("publish_statistics(): publicando estadisticas")

        stats = {}
        stats['llamadas_en_curso'] = self._campana_call_status.\
            get_count_llamadas()
        stats['campanas_en_ejecucion'] = self._campana_call_status.\
            count_trackers_activos
        stats['running'] = True
        # TODO: usar time.clock() u alternativa
        stats['time'] = time.time()
        self._statistics_service.publish_statistics(stats)

    #
    # Eventos
    #

    def onCampanaNoEnEjecucion(self, campana):
        """Ejecutado por generator() cuando se detecta
        CampanaNoEnEjecucion. Esto implica algunas de las siguientes
        situaciones:
        1. la campana que se estaba por ejecutar, NO debio tenerse en cuenta
           (posible bug?)
        2. justo se ha vencido (por fecha de fin de la campaña,
           u hora de actuacion)
        3. simplemente alguien ha pausado la campaña

        Banea a la campana
        """
        self._campana_call_status.banear_campana(campana)
        logger.debug("onCampanaNoEnEjecucion: %s", campana.id)

    def onNoMasContactosEnCampana(self, campana):
        """Ejecutado por generator() cuando se detecta
        NoMasContactosEnCampana. Esto implica que la campana que se
        estaba teniendo en cuenta en realidad no posee contactos
        a procesar.

        Esta situacion puede parser inicialmente parecida a
        `TodosLosContactosPendientesEstanEnCurso`, pero NO.
        `TLCPEEC` implica que no se pueden procesar los pendientes.
        `NoMasContactosEnCampana` implica que la campaña ya no
        posee pendientes, está terminada.

        Banea a la campana
        """
        logger.debug("onNoMasContactosEnCampana() para la campana %s.",
            campana.id)
        self._campana_call_status.banear_campana(campana,
            reason=BANEO_NO_MAS_CONTACTOS, forever=True)

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

    def onLimiteDeOriginatePorSegundosError(self, to_sleep):
        """Ejecutado por generator() cuando detecta que hay que realizar
        una espera, debido a que se alcanzo el limite de ORIGINATEs por
        segundos.

        Esto no deberia suceder, pero hay algunos corner cases, por ejemplo,
        la actuacion o la campaña se vencieron justo mientras se estaban
        por procesar.
        """
        logger.info("onLimiteDeOriginatePorSegundosError(): hará falta "
            "esperar %s seg. para no superar el limite "
            "de ORIGINATEs por segundo", to_sleep)

    def onTodosLosContactosPendientesEstanEnCursoError(self, campana):
        """Ejecutado por generator() cuando detecta que, aunque hay contactos
        pendientes, éstos ya están con llamadas en curso actualmente, y por
        lo tanto, no podemos volver a intentarlos.
        """
        logger.info("onTodosLosContactosPendientesEstanEnCursoError(): "
            "todos los contactos pendientes de la campana %s poseen "
            "llamadas en curso. Se baneara la campana.", campana.id)

        self._campana_call_status.banear_campana(campana,
            reason=BANEO_TODOS_LOS_PENDIENTES_EN_CURSO)

        #
        # ACTUALIZADO: ahora hemos refactorizado muchas cosas. El
        # siguiente comentario ya no es válido. Lo dejamos por un
        # tiempo SOLO COMO REFERENCIA.
        #
        #
        #
        ## ----- Versión corta
        ##
        ##  - ESTO ESTA MAL! No deberiamos eliminar la campaña, y
        ##    deberiamos refactorizar el manejo del baneo
        ##
        ## ----- Versión larga
        ##
        ## En vez eliminar campaña del tracker, el control de baneo
        ## debería moverse al loop() de generator(), así las campañas baneadas
        ## no son ignoradas por los otros metodos (^1), y permitimos que
        ## se actualice el 'status' de estas campañas.
        ##
        ## (^1) sobre todo, ahora necesitamos que refrescar_channel_status()
        ##      NO ignore las campañas baneadas por
        ##      BANEO_TODOS_LOS_PENDIENTES_EN_CURSO, todo lo contrario!
        ##      Necesitamos que lo antes posible se actualice el status
        ##      para intentar los contactos pendientes.
        #
        #        try:
        #            del self.trackers_campana[campana]
        #        except KeyError:
        #            pass

    def onLimiteGlobalDeCanalesAlcanzadoError(self):
        """Ejecutado por generator() cuando se detecta
        que la cantidad de canales utilizado ha llegado al limite.

        El limite esta configurado a travez de settings, con la variable
        FTS_LIMITE_GLOBAL_DE_CANALES.

        Este evento no debe confundirse con onLimiteDeCanalesAlcanzadoError(),
        este ultimo se produce cuando se alcaza el limite para una campaña
        en particular!
        """
        logger.debug("onLimiteGlobalDeCanalesAlcanzadoError(): limite "
            "alcanzado")

    def onTodasLasCampanasAlLimite(self):
        """Ejecutado por generator() cuando se detecta que todas las campañas
        estan al limite de su ejecucion.
        """
        logger.debug("onTodasLasCampanasAlLimite(): todas las campanas"
            " estan al limite")

    def real_sleep(self, espera):
        """Metodo que realiza la espera real Si ``espera`` es < 0,
        no hace nada
        """
        if espera > 0:
            self.publish_statistics()
            time.sleep(espera)

    def sleep(self, espera):
        """Produce espera de (al menos) ``espera`` segundos. Mientras
        espera, ejecuta ciertos procesos que no conviene ejecutar mientras
        se procesan llamadas.
        """
        # TODO: usar time.clock() u alternativa
        inicio = time.time()
        for campana in self._campana_call_status.obtener_baneados_por_razon(
            BANEO_NO_MAS_CONTACTOS):

            logger.debug("sleep(): evaluando si finalizamos la campana %s",
                campana.id)
            delta = time.time() - inicio
            if delta >= espera:
                # Si nos pasamos de `segundos`, salimos
                logger.info("sleep(): ya superamos el tiempo de espera "
                    "solicitado. No finalizaremos la campana %s, y "
                    "continuaremos la ejecucion del loop", campana.id)
                return

            self._finalizador_de_campanas(campana.id)
            self._campana_call_status.banear_campana(campana,
                reason=BANEO_CAMPANA_FINALIZADA, forever=True)

        delta = time.time() - inicio
        self.real_sleep(espera - delta)

    def generator(self):
        """Devuelve los datos de contacto a contactar, de a una
        campaña por vez.

        :returns: (campana, contacto_id, telefono, cant_intentos_realizados)
        """

        iter_num = 0

        while True:

            if self.max_iterations is not None:
                iter_num += 1
                if iter_num >= self.max_iterations:
                    raise CantidadMaximaDeIteracionesSuperada("Se supero la "
                        "cantidad maxima de iteraciones: {0}".format(
                            self.max_iterations))

            # Publicamos estadisticas si corresponde
            self.publish_statistics()

            #==================================================================
            # [1] Actualizamos trackers de campaña
            #==================================================================

            # Obtiene las campañas que pueden ser procesadas
            # Si no hay campañas, espseramos y reiniciamos.
            trackers_activos = \
                self._campana_call_status.obtener_trackers_para_procesar()

            if not bool(trackers_activos):
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
                # TODO: esto es asi porque, todavia, no exponemos el status
                #  a la web!
                continue

            #==================================================================
            # [2] Refrescamos status de conexiones
            #==================================================================

            # Este refresco tambien se hace en el loop
            self._asterisk_call_status.\
                refrescar_channel_status_si_es_necesario()

            # Si TODAS las campañas han llegado al límite, no tiene sentido
            # hacer un busy wait... mejor esperamos
            # +----------------------------------------------------------------
            # | Los eventos que deberian despertar este 'sleep' son:
            # | 1. se ha finalizado la llamada de cualquiera de las
            # |    campañas q' habian llegado al limite
            # +----------------------------------------------------------------

            if self._campana_call_status.todas_las_campanas_al_limite():
                self.onTodasLasCampanasAlLimite()
                logger.info("Todas las campañas han llegado al límite. "
                    "Esperamos %s segs. y reiniciamos round",
                    settings.FTS_DAEMON_SLEEP_LIMITE_DE_CANALES)
                self.sleep(settings.FTS_DAEMON_SLEEP_LIMITE_DE_CANALES)
                # Reiniciamos con la esperaza de que se actualizan trackers
                # y status
                continue

            # Si se ha alcanzado el limite global de campañas, tampoco tiene
            # sentido hacer un busy wait
            # +----------------------------------------------------------------
            # | Los eventos que deberian despertar este 'sleep' son:
            # | 1. se ha liberado un canal
            # +----------------------------------------------------------------

            # ATENCION: esta misma logica (o muy parecida) se usa en el loop
            if self._campana_call_status.limite_global_de_canales_alcanzado():
                logger.debug("Se ha alcanzado el limite global de canales. "
                    "Esperamos %s segs. y reiniciamos round",
                    settings.FTS_ESPERA_POR_LIMITE_GLOBAL_DE_CANALES)
                self.onLimiteGlobalDeCanalesAlcanzadoError()
                self.real_sleep(settings.\
                    FTS_ESPERA_POR_LIMITE_GLOBAL_DE_CANALES)
                # Reiniciamos para ver si se actualizan trackers y status
                continue

            ##
            ## Procesamos...
            ##

            loop__contactos_procesados = 0
            loop__TLCPEECE_detectado = False
            loop__limite_de_campana_alcanzado = False
            loop__campana_ignorada_x_limite_global = False

            # Trabajamos en copia, por si hace falta modificarse
            for tracker_campana in trackers_activos:

                # Publicamos estadisticas si corresponde
                self.publish_statistics()

                # Si la campana esta al limite, la ignoramos
                if tracker_campana.limite_alcanzado():
                    logger.debug("Ignorando campana %s porque esta al limite",
                        tracker_campana.campana.id)
                    loop__limite_de_campana_alcanzado = True
                    continue

                #==============================================================
                # Chequeamos limite global de llamadas en curso
                #==============================================================

                if self._campana_call_status.\
                    limite_global_de_canales_alcanzado():

                    self.onLimiteGlobalDeCanalesAlcanzadoError()
                    loop__esperas_por_limite_global = 0

                    try:
                        # Esperamos un poco, con la intensión de que se
                        # desocupe algun canal.
                        # De este while se sale de 2 formas:
                        # 1) luego de varias iteraciones, si no pasa nada,
                        #    salimos y continuamos con otra campaña,
                        #    para esto usamos ContinueOnOuterWhile()
                        # 2) se detecto que hay canales libres, se sale
                        #    con un break del loop, y continuamos el
                        #    procesamiento normal de la campaña
                        while True:
                            loop__esperas_por_limite_global += 1
                            # Somos más agresivos, usamos 'si_es_posible'
                            self._asterisk_call_status.\
                                refrescar_channel_status_si_es_posible()

                            # Condicion de corte
                            if not self._campana_call_status.\
                                limite_global_de_canales_alcanzado():
                                break  # break 'while True'

                            # Condicion de corte
                            if loop__esperas_por_limite_global >= 10:
                                raise ContinueOnOuterWhile()

                            # Esperamos...
                            self.real_sleep(settings.\
                                FTS_ESPERA_POR_LIMITE_GLOBAL_DE_CANALES)

                        # Salimos del whlie (loop) sin excepcion!
                        # Implica que hay canales libres :-)
                        logger.info("generator(): ya no excedemos el "
                            "limite global de canales, continuamos...")

                    except ContinueOnOuterWhile:
                        loop__campana_ignorada_x_limite_global = True
                        logger.warn("generator(): luego de %s loops, todavia"
                            "no podemos continuar porque se ha alcanzado"
                            "el limite global de canales. Continuamos "
                            "con campana siguiente",
                            loop__esperas_por_limite_global)
                        continue

                #==============================================================
                # Chequeamos limite de llamadas por segundo
                #==============================================================
                time_to_sleep = self._originate_throttler.time_to_sleep()
                if time_to_sleep > 0.0:
                    self.onLimiteDeOriginatePorSegundosError(time_to_sleep)
                    self.real_sleep(time_to_sleep)
                    # TODO: podriamos actualizar el status
                    # para aprovechar este tiempo de espera

                try:
                    yield tracker_campana.next()
                    loop__contactos_procesados += 1
                except TodosLosContactosPendientesEstanEnCursoError:
                    self.onTodosLosContactosPendientesEstanEnCursoError(
                        tracker_campana.campana)
                    loop__TLCPEECE_detectado = True
                except CampanaNoEnEjecucion:
                    self.onCampanaNoEnEjecucion(tracker_campana.campana)
                except NoMasContactosEnCampana:
                    # Esta excepcion es generada cuando la campaña esta
                    # en curso (el estado), pero ya no tiene pendientes
                    # FIXME: aca habria q' marcar la campana como finalizada?
                    # El tema es que puede haber llamadas en curso, pero esto
                    # no deberia ser problema...
                    self.onNoMasContactosEnCampana(tracker_campana.campana)
                except LimiteDeCanalesAlcanzadoError:
                    # ESTO NO DEBERIA SUCEDER! No debio ejecutarse
                    # tracker.next() si la campaña estaba al limite
                    logger.exception("Se detecto "
                        "LimiteDeCanalesAlcanzadoError al procesar la campana "
                        "{0}, pero nunca debio intentarse obtener un contacto "
                        "de esta campana si estaba al limite".format(
                            tracker_campana.campana.id))
                    self.onLimiteDeCanalesAlcanzadoError(
                        tracker_campana.campana)

            # Si se detecta 'TodosLosContactosPendientesEstanEnCursoError',
            # o se ignoro campaña porque llegó al límite de llamadas,
            # y hay una sola campaña en ejecucion, entonces puede
            # suceder q' no se haya procesado ningun contacto
            if loop__contactos_procesados == 0:
                causas_ok = any([
                    loop__TLCPEECE_detectado,
                    loop__limite_de_campana_alcanzado,
                    loop__campana_ignorada_x_limite_global,
                ])
                if not causas_ok:
                    # Si no se detecto ninguna causa que pueda generar
                    # que no se produzca el procesamineto de ningun
                    # contacto, logueamos un warn()
                    logger.warn("No se ha devuelto ningun contacto en el "
                        "ROUND actual")
                    self.onNoSeDevolvioContactoEnRoundActual()


class Llamador(object):
    """Utiliza RoundRobinTracker para obtener números a contactar,
    y realiza los llamados.
    """

    def __init__(self):
        self.rr_tracker = RoundRobinTracker()

    def procesar_contacto(self, *args, **kwargs):
        return llamador_contacto.procesar_contacto(*args, **kwargs)

    def run(self, max_loops=0):
        """Inicia el llamador"""
        current_loop = 1
        for campana, id_contacto, numero, cant_intentos in \
            self.rr_tracker.generator():
            logger.debug("Llamador.run(): campana: %s - id_contacto: %s"
                " - numero: %s", campana, id_contacto, numero)

            originate_ok = self.procesar_contacto(campana, id_contacto, numero,
                cant_intentos)
            self.rr_tracker.originate_throttler.set_originate(originate_ok)

            current_loop += 1
            if max_loops > 0 and current_loop > max_loops:
                logger.info("Llamador.run(): max_loops alcanzado. Exit!")
                return
