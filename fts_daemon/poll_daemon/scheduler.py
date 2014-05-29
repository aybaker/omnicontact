# -*- coding: utf-8 -*-
"""

"""

from __future__ import unicode_literals

from datetime import datetime, timedelta
import time

from django.conf import settings
from fts_daemon.asterisk_ami_http import AmiStatusTracker
from fts_daemon.llamador_contacto import procesar_contacto
from fts_daemon.poll_daemon.ban_manager import BanManager
from fts_daemon.poll_daemon.campana_tracker import CampanaTracker, \
    CampanaNoEnEjecucion, NoMasContactosEnCampana, \
    LimiteDeCanalesAlcanzadoError, TodosLosContactosPendientesEstanEnCursoError
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


class NoHayCampanaEnEjecucion(Exception):
    """No se encontraron campanas en ejecucion. O si hay campañas,
    estan baneadas.
    """


# TODO: renombrar OriginateThrottler a OriginateThrottler
class OriginateThrottler(object):
    """Keeps the status of ORIGINATEs and the limits of
    allowed ORIGINATEs per seconds
    """

    def __init__(self):
        # self._originate_ok = datetime.now() - timedelta(days=30)
        self._originate_ok = None
        if settings.FTS_DAEMON_ORIGINATES_PER_SECOND > 0.0:
            self._orig_per_sec = settings.FTS_DAEMON_ORIGINATES_PER_SECOND
            self._max_wait = 1.0 / self._orig_per_sec
        else:
            logger.info("OriginateThrottler: limite desactivado")
            self._orig_per_sec = None
            self._max_wait = None

    # TODO: renombrar a "set_originate_succesfull" o "originate_succesfull"
    def set_originate(self, ok):
        """Set that originate was succesfull or not"""
        if ok:
            self._originate_ok = datetime.now()
        else:
            self._originate_ok = None

    def time_to_sleep(self):
        """How many seconds to wait, to not exceed the limit
        `FTS_DAEMON_ORIGINATES_PER_SECOND`
        """
        if self._originate_ok == None or self._orig_per_sec is None:
            # Primera vez q' se usa, o no hay limite configurado
            return 0.0

        # Calculamos timedelta
        td = datetime.now() - self._originate_ok
        if td.days < 0 or td.days > 0:
            # paso algo raro... esperamos `self._max_wait`
            logger.warn("OriginateThrottler.time_to_sleep(): valor sospechoso "
                "de td.days: %s", td.days)
            return self._max_wait

        # td.days == 0, ahora calculamos `delta` en segundos
        delta = float(td.seconds) + float(td.microseconds) / 1000000.0

        # Si el delta es < 0, paso algo raro!
        if delta < 0.0:
            # paso algo raro... esperamos `self._max_wait`
            logger.warn("OriginateThrottler.time_to_sleep(): valor sospechoso "
                "de delta: %s", delta)
            return self._max_wait

        # Si el delta es > a espera maxima, no esperamos mas
        if delta >= self._max_wait:
            return 0.0

        # Calculamos cuanto tiempo hay que esperar
        to_sleep = self._max_wait - delta
        return to_sleep


class CampanaCallStatus(object):
    """Traquea el status de todas las campañas en conjunto."""

    def __init__(self):
        """Constructor"""

        self._trackers_campana_dict = {}
        """Diccionario con los trackers de las campañas siendo procesadas.
        :key: :class:`fts_web.models.Campana`
        :value: :class:`.CampanaTracker`
        """

        self._trackers_activos = []
        """Lista de trackers activos"""

        self._ban_manager = BanManager()
        """Administrador de baneos"""

        # TODO: usar time.clock() u alternativa
        self._ultimo_refresco_trackers = datetime.now() - timedelta(days=30)
        """Ultima vez q' se consulto la BD, para refrescar los
        trackers. Es usado por necesita_refrescar_trackers() y
        refrescar_trackers()
        """

    def banear_campana(self, campana_u_objeto, reason=None,
        forever=False):
        return self._ban_manager.banear_campana(campana_u_objeto,
            reason=reason, forever=forever)

    def obtener_baneados_por_razon(self, reason):
        return self._ban_manager.obtener_por_razon(reason)

    def _obtener_campanas_en_ejecucion(self):
        """Devuelve campañas en ejecucion. Las busca en la BD"""
        return Campana.objects.obtener_ejecucion()

    def _necesita_refrescar_trackers(self):
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

        # FIXME: mover a settings
        # TODO: usar time.clock() u alternativa
        delta = datetime.now() - self._ultimo_refresco_trackers
        if delta.days > 0 or delta.seconds > 10:
            return True
        return False

    def refrescar_trackers_activos(self):
        """Revisa si algun tracker activo fue baneado, y actualiza trackers.

        Este metdodo *NO ACCEDE A LA BD*.
    
        Esto hace falta porque, entre ejecuciones del loop(), las campanas
        pueden ser baneadas, y si este metodo no existiera, serian evaluadas
        una y otra vez por el loop() hasta que se vuelva a ejecutar
        `refrescar_trackers()`.

        :raises: NoHayCampanaEnEjecucion
        """

        for tracker in self._trackers_activos:
            if self._ban_manager.esta_baneada(tracker.campana):
                logger.debug("refrescar_trackers_activos(): campana %s esta "
                    " baneada", tracker.campana.id)
                # Esta baneada! Desactivamos...
                tracker.desactivar()

        self._trackers_activos = [tracker
            for tracker in self._trackers_campana_dict.values()
                if tracker.activa]

        if not self._trackers_activos:
            raise NoHayCampanaEnEjecucion()

    def refrescar_trackers(self):
        """Refresca la lista de trackers de campañas
        (self._trackers_campana_dict), incluye buscar en BD las campañas
        en ejecucion.

        Se crean instancias de CampanaTracker SOLO para las nuevas campañas.
        Las instancias de CampanaTracker para campañas que ya están siendo
        traqueadas son mantenidas. Las instancias de CampanaTracker de campañas
        que ya no son más trackeadas, son marcadas como desactivadas.

        Este metodo siempre utiliza la versión recién obtenida de Campana
        para los KEYs; esto es necesario por si la campaña cambia de estado.

        :raises: NoHayCampanaEnEjecucion
        """
        logger.debug("refrescar_trackers(): Iniciando...")
        self._ultimo_refresco_trackers = datetime.now()

        # Es importante crear un NUEVO diccionario, para asegurarnos que
        # las claves sean la version MAS RECIENTE (recien traidas de
        # la BD) de instancias de Campaña, por si cambio el estado,
        # por ejemplo. Y para ser consistentes, ademas, actualizamos
        # la instancia en CampanaTracker, usando `update_campana()`
        previous_trackers = dict(self._trackers_campana_dict)
        current_trackers = {}

        for campana in self._obtener_campanas_en_ejecucion():

            logger.debug("refrescar_trackers(): evaluando %s",
                campana.id)

            # Si está baneada...
            if self._ban_manager.esta_baneada(campana):
                logger.debug("refrescar_trackers(): campana %s esta baneada",
                    campana.id)

                try:
                    current_trackers[campana] = previous_trackers[campana]
                except KeyError:
                    current_trackers[campana] = CampanaTracker(campana)
                    # La creamos activa, y despues la desactivamos... no es
                    # lo mas eficiente, pero tampoco es para tanto!

                # Esta baneada! Nos aseguramos q' quede desactiva
                current_trackers[campana].update_campana(campana)
                current_trackers[campana].desactivar()
                continue

            # Si existe desde antes, y no esta baneada: reactivamos
            if campana in previous_trackers:
                # Ya existia de antes, la reutilizamos
                logger.debug("refrescar_trackers(): reutilizando tacker "
                    "para campana %s", campana.id)
                current_trackers[campana] = previous_trackers[campana]
                current_trackers[campana].reactivar_si_corresponde(campana)
                continue

            # Es nueva...
            logger.debug("refrescar_trackers(): nueva campana: %s",
                campana.id)
            current_trackers[campana] = CampanaTracker(campana)

        # Desactivamos y logueamos campanas q' no van mas...
        for campana in previous_trackers:
            if campana in current_trackers:
                # Si existe en `current_trackers`, la ignoramos
                continue

            logger.info("refrescar_trackers(): desactivando tracker para "
                "campana %s", campana.id)
            current_trackers[campana] = previous_trackers[campana]
            current_trackers[campana].update_campana(campana)
            current_trackers[campana].desactivar()

        del previous_trackers  # Ya no hace falta

        # Luego de procesar y loguear todo, si vemos q' no hay trackers
        # activos, lanzamos excepcion
        self._trackers_campana_dict = current_trackers
        self._trackers_activos = [tracker
            for tracker in current_trackers.values()
                if tracker.activa]

        if not self._trackers_activos:
            raise NoHayCampanaEnEjecucion()

    def todas_las_campanas_al_limite(self):
        """Chequea trackers y devuelve True si TODAS las campañas
        en curso estan al limite"""
        al_limite = [tracker.limite_alcanzado()
            for tracker in self._trackers_activos]

        if al_limite and all(al_limite):
            return True
        return False

    def onNoHayCampanaEnEjecucion(self):
        """Ejecutado cuando se detecta NoHayCampanaEnEjecucion."""
        logger.debug("No hay campanas en ejecucion.")

    def obtener_trackers_para_procesar(self):
        """Actualiza trackers (si corresponde) y devuelve trackers activos
        para las que hay que generar llamadas. ATENCION: devuelve tambien
        trackers de campañas que están al limite.

        Este metodo podria ser más 'inteligente', y devolver SOLO los
        trackers para los cuales realmente se pueden hacer llamadas.
        Esto lo dejamos para futuras refactorizaciones.
        """
        # FIXME: chequear limite de llamadas de campanas
        # FIXME: chequear baneos

        try:
            if self._necesita_refrescar_trackers():
                self.refrescar_trackers()  # -> NoHayCampanaEnEjecucion
            else:
                # Aunque no vayamos a la BD, puede haber habido baneos!
                # asi q' tenemos q' actualizar igual
                self.refrescar_trackers_activos()  # -> NoHayCampanaEnEjecucion
        except NoHayCampanaEnEjecucion:
            self.onNoHayCampanaEnEjecucion()

        return list(self._trackers_activos)

    @property
    def trackers_activos(self):
        """Devuelve lista de trackers activos. NO intenta actualizar.
        Si hace falta intentar actualizar, usar
        `obtener_trackers_para_procesar()`
        """
        return list(self._trackers_activos)

    def update_call_status(self, full_status):
        """
        Guarda la informacion de las llamadas en curso (`full_status`)
        en los trackers asociados a las distintas llamadas, creando
        los trackers que sean necesarios.

        Luego de llamar esta funcion, toda la informacion de las llamadas
        es guardada en algún lugar. Por lo tanto, la informacion en los
        trackers se podrá utilizar para controlar el limite global de
        llamadas.
        """
        # full_status -> dict
        #  * KEY -> campana_id
        #  * VALUE -> [
        #        [contacto_id, numero, campana_id],
        #        [contacto_id, numero, campana_id],
        #    ]

        not_updated = dict(self._trackers_campana_dict)
        by_id = dict([(c.id, c) for c in self._trackers_campana_dict])

        for campana_id, items in full_status:
            contactos = [item[0] for item in items]

            # Si existe, actualizamos los valores
            if campana_id in by_id:
                logger.debug("update_call_status(): actualizando llamadas en "
                    "curso para la campana %s", campana_id)
                campana = by_id[campana_id]
                tracker = self._trackers_campana_dict[campana]
                tracker.contactos_en_curso = contactos
                del not_updated[campana]
                continue

            # No existe tracker para campana `campana_id`
            logger.debug("update_call_status(): creando tracker y seteando "
                "llamadas en curso para la campana %s", campana_id)
            Campana = Campana.objects.get(pk=campana_id)
            tracker = CampanaTracker(campana)
            tracker.desactivar()
            self._trackers_campana_dict[campana] = tracker

        # Aca procesamos todas las campanas incluidas en `full_status`
        # PERO puede haber campanas q' no poseen llamadas en curso!
        # Ahora las actualizamos...
        for campana, tracker in not_updated.iteritems():
            logger.info("update_call_status(): no se recibieron "
                "datos para la campana %s... Suponemos que no hay "
                "llamadas en curso para dicha campana", tracker.campana.id)
            tracker = self._trackers_campana_dict[campana]
            tracker.contactos_en_curso = []

    def get_count_llamadas(self):
        """Devuelve el count total (APROXIMADO) de llamadas en curso."""
        count = 0
        for tracker in self._trackers_campana_dict.values():
            count += tracker.llamadas_en_curso_aprox
        return count

    def limite_global_de_canales_alcanzado(self):
        """Chequea si se ha alcanzado/excedido el limite global de
        canales
        """
        if self.get_count_llamadas() >= \
            settings.FTS_LIMITE_GLOBAL_DE_CANALES:
            return True
        else:
            return False


class AsteriskCallStatus(object):
    """Encapsula informacion de fecha de ultimo status via AMI, y
    mantiene toda la informacion que devolvio la ultima consulta
    exitosa"""

    def __init__(self, campana_call_status):
        self._ultimo_intento_refresco = datetime.now() - timedelta(days=30)
        # self._ultimo_refresco = None

        # self._full_status = {}
        # NO guardamos esta info, porque la info más actualizada
        # está en los trackers!!!! (ya que estos trackers son actualizados
        # con los nuevos ORIGINATES producidos)

        self._ami_status_tracker = AmiStatusTracker()
        """Status tracker via HTTP AMI"""

        self._campana_call_status = campana_call_status

    def touch(self):
        """Actualiza timestamp de ultimo intento de refresco"""
        # TODO: usar time.clock() u alternativa
        self._ultimo_intento_refresco = datetime.now()

    def puede_refrescar(self):
        """Devuelve si el tracker se debe/puede refrescar o no, teniendo
        en cuenta solamente la fecha/hora del ultimo refresco.
        """
        delta = datetime.now() - self._ultimo_intento_refresco
        # No hacemos más de 1 consulta cada 3 segundos

        if delta.days == 0 and delta.seconds < 3:
            return False
        else:
            return True

    def refrescar_channel_status_si_es_posible(self):
        """Si puede refrescar, refresca"""
        if self.puede_refrescar():
            self.refrescar_channel_status()

    def refrescar_channel_status_si_es_necesario(self):
        """Si necesita refrescar, refresca"""
        if self.necesita_refrescar_channel_status():
            self.refrescar_channel_status()

    def necesita_refrescar_channel_status(self):
        """Devuelve booleano indicando si debe y es conveniente refrescar
        el status de los channels de Asterisk.

        Este metodo SOLO tiene en cuenta los limites de canales de las
        campañas, por lo tanto, solo devolvera True si alguna de las
        campañas está al límite.

        Por lo tanto, NO SIRVE para refrescar el status cuando se ha
        alcanzado el limite GLOBAL, y estamos esperando que se liberen
        canales, ya que puede ser que, aunque se haya alcanzado el
        limite GLOBAL, ninguna de las campañas haya alcanzado el limite.

        QUIZA lo mejor sea que este metodo NO EXISTA, y solo chequear
        el tiempo de la ultima actualizacion (o sea, siempre actualizar,
        excepto si la ultima actualizacion fue hace poco), aunque no deja
        de ser una optimizacion interesante, para no perder tiempo cuando
        estamos haciendo originates.
        """
        trackers_activos = self._campana_call_status.trackers_activos
        if not trackers_activos:
            logger.debug("necesita_refrescar_channel_status(): no actualizamos"
                " porque no hay trackers activos")
            return False

        if not self.puede_refrescar():
            logger.debug("necesita_refrescar_channel_status(): no actualizamos"
                " porque la ultima actualizacion fue recientemente")
            return False

        # Si llegamos aca, es porque `trackers_activos` NO esta vacio
        al_limite = [tr.limite_alcanzado() for tr in trackers_activos]

        # any(): si empty, return False
        if any(al_limite):
            pass  # Hay al menos 1 al limite
        else:
            # Ninguna esta al limite
            logger.debug("necesita_refrescar_channel_status(): no actualizamos"
                " porque no se alcanzo el limite en ninguna campaña")
            return False

        # DEBUG: si todas las campañas estan al limite, lo logueamos
        if all(al_limite):
            logger.debug("necesita_refrescar_channel_status(): todas las "
                "campañas estan al limite")

        logger.debug("necesita_refrescar_channel_status(): True")
        return True

    def refrescar_channel_status(self):
        """Refresca `contactos_en_curso` de `self.trackers_campana`.

        En caso de error, no actualiza ningun valor.
        """
        # Antes q' nada, actualizamos 'ultimo refresco'
        self.touch()

        logger.info("Actualizando status via AMI HTTP")
        try:
            full_status = self._ami_status_tracker.\
                get_status_por_campana()
        except:
            logger.exception("Error detectado al ejecutar "
                "ami_status_tracker.get_status_por_campana(). Los statuses "
                "no seran actualizados")
            return

        # Actualizamos trackers
        self._campana_call_status.update_call_status(full_status)


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

        self.trackers_campana = {}
        """Diccionario con los trackers de las campañas siendo procesadas.

        :key: :class:`fts_web.models.Campana`
        :value: :class:`.CampanaTracker`
        """

        self.ami_status_tracker = AmiStatusTracker()
        """Status tracker via HTTP AMI"""

        self.ban_manager = BanManager()
        """Administrador de baneos"""

        self._originate_throttler = OriginateThrottler()
        """Administrador de limites de originates por segundo"""

        # Quiza esto deberia estar en `self.trackers_campana`
        # TODO: usar time.clock() u alternativa
        self._ultimo_refresco_trackers = datetime.now() - timedelta(days=30)
        """Ultima vez q' se consulto la BD, para refrescar los
        trackers. Es usado por necesita_refrescar_trackers() y
        refrescar_trackers()
        """

        self._asterisk_call_status = AsteriskCallStatus()

        self.max_iterations = None
        """Cantidad de interaciones maxima que debe realizar ``generator()``.
        Si vale ``None``, no se realiza ningun control.
        Sino, al alcanzar esa cantidad de iteraciones, generator() hace
        return"""

    @property
    def originate_throttler(self):
        return self._originate_throttler

    @originate_throttler.setter
    def originate_throttler(self, new_value):
        assert settings.FTS_TESTING_MODE, "No esta permitido cambiar " \
            "'originate_throttler' cuando no se esta en FTS_TESTING_MODE"
        self._originate_throttler = new_value

    #
    # Refresco de TRACKERS
    #

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

        # TODO: usar time.clock() u alternativa
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
        traqueadas son mantenidas. Las instancias de CampanaTracker de campañas
        que ya no son más trackeadas, son eliminadas.

        :raises: NoHayCampanaEnEjecucion
        """
        logger.debug("refrescar_trackers(): Iniciando...")
        self._ultimo_refresco_trackers = datetime.now()
        old_trackers = dict(self.trackers_campana)
        new_trackers = {}
        for campana in self._obtener_campanas_en_ejecucion():

            if self.ban_manager.esta_baneada(campana):
                logger.debug("Ignorando campana %s xq esta baneada",
                    campana.id)
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

    #
    # Refresco de STATUS via AMI
    #

    def refrescar_channel_status(self):
        """Refresca `contactos_en_curso` de `self.trackers_campana`.

        En caso de error, no actualiza ningun valor.
        """

        # Antes q' nada, actualizamos 'ultimo refresco'
        self._asterisk_call_status.touch()

        logger.info("Actualizando status via AMI HTTP")
        try:
            new_status = self.ami_status_tracker.get_status_por_campana()
        except:
            logger.exception("Error detectado al ejecutar "
                "ami_status_tracker.get_status_por_campana(). Los statuses "
                "no seran actualizados")
            return

        # Guardamos ultimo status en asterisk_call_status
        self._asterisk_call_status.full_status = dict(new_status)

        # Actualizamos `self.trackers_campana`
        for tracker in self.trackers_campana.values():
            self._asterisk_call_status.update_campana_tracker(tracker)

    #
    # Eventos
    #

    def onNoHayCampanaEnEjecucion(self):
        """Ejecutado por generator() cuando se detecta
        NoHayCampanaEnEjecucion.
        """
        logger.debug("No hay campanas en ejecucion.")

    def onCampanaNoEnEjecucion(self, campana):
        """Ejecutado por generator() cuando se detecta
        CampanaNoEnEjecucion. Esto implica algunas de las siguientes
        situaciones:
        1. la campana que se estaba por ejecutar, NO debio tenerse en cuenta
           (posible bug?)
        2. justo se ha vencido (por fecha de fin de la campaña,
           u hora de actuacion)
        3. simplemente alguien ha pausado la campaña

        Banea a la campana, y la elimina de `self.trackers_campana`
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

        Banea a la campana, y la elimina de `self.trackers_campana`
        """
        logger.debug("onNoMasContactosEnCampana() para la campana %s.",
            campana.id)
        self.ban_manager.banear_campana(campana, reason=BANEO_NO_MAS_CONTACTOS)
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

        self.ban_manager.banear_campana(campana,
            reason=BANEO_TODOS_LOS_PENDIENTES_EN_CURSO)

        #
        # ----- Versión corta
        #
        #  - ESTO ESTA MAL! No deberiamos eliminar la campaña, y
        #    deberiamos refactorizar el manejo del baneo
        #
        # ----- Versión larga
        #
        # En vez eliminar campaña del tracker, el control de baneo
        # debería moverse al loop() de `generator()`, así las campañas baneadas
        # no son ignoradas por los otros metodos (^1), y permitimos que
        # se actualice el 'status' de estas campañas.
        #
        # (^1) sobre todo, ahora necesitamos que refrescar_channel_status()
        #      NO ignore las campañas baneadas por
        #      BANEO_TODOS_LOS_PENDIENTES_EN_CURSO, todo lo contrario!
        #      Necesitamos que lo antes posible se actualice el status
        #      para intentar los contactos pendientes.
        #

        try:
            del self.trackers_campana[campana]
        except KeyError:
            pass

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

    def finalizar_campana(self, campana_id):
        campana = Campana.objects.get(pk=campana_id)

        if campana.estado != Campana.ESTADO_ACTIVA:
            logger.info("finalizar_campana(): No finalizaremos campana "
                "%s porque su estado no es ESTADO_ACTIVA", campana.id)
            try:
                del self.trackers_campana[campana]
            except KeyError:
                pass
            self.ban_manager.eliminar(campana)
            return

        # LIMITE = settings.FTS_MARGEN_FINALIZACION_CAMPANA
        logger.info("finalizar_campana(): finalizando campana %s", campana.id)

        campana.finalizar()

    def real_sleep(self, espera):
        """Metodo que realiza la espera real Si ``espera`` es < 0,
        no hace nada
        """
        if espera > 0:
            time.sleep(espera)

    def sleep(self, espera):
        """Produce espera de (al menos) ``espera`` segundos. Mientras
        espera, ejecuta ciertos procesos que no conviene ejecutar mientras
        se procesan llamadas.
        """
        # TODO: usar time.clock() u alternativa
        inicio = time.time()
        for campana in self.ban_manager.obtener_por_razon(
            BANEO_NO_MAS_CONTACTOS):

            logger.debug("sleep(): evaluando si finalizamos la campana %s",
                campana.id)
            if time.time() - inicio >= espera:
                # Si nos pasamos de `segundos`, salimos
                logger.info("sleep(): ya superamos el tiempo de espera "
                    "solicitado! No finalizaremos la campana %s", campana.id)
                return

            self.finalizar_campana(campana.id)

        delta = time.time() - inicio
        self.real_sleep(espera - delta)

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

        En el loop, las consultas (a BD y Asterisk) se realizan asi:

        +---------------------------+
        | [1] refrescar_trackers()  | --> self.trackers_campana
        +---------------------------+

          ||
          \/

        +---------------------------------+
        | [2] refrescar_channel_status()  | --> self._asterisk_call_status
        +---------------------------------+

          ||
          \/

        +--------------------------+
        | proceso de las campañas  |
        +--------------------------+

          ||
          \/

        +----------------------+
        | finalizar_campana()  | --> del self.trackers_campana[x]
        | onXxxx()             |
        +----------------------+


        Pero las actualizaciones de [1] y [2] no se realiza siempre. En cada
        ejecucion del loop, puede ejecutarse sólo [1], sólo [2],
        ambas o ninguna... y todas las decisiones se basan en estos datos.

        Pero algo a tener en cuenta es que `refrescar_channel_status()` está
        pensado para ser ejecutado despues de `refrescar_trackers()`, por lo
        tanto, deberia ser seguro ejecutar `refrescar_channel_status()`
        varias veces en un mismo loop.

        PERO algunos metodos ELIMINAN instancias de `self.trackers_campana`.
        ** ESTE ES EL PROBLEMA A SOLUCIONAR **

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

            #==================================================================
            # [1] Actualizamos trackers de campaña
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
            # [2] Refrescamos status de conexiones
            #==================================================================

            # Este refresco tambien se hace en el loop
            if self._asterisk_call_status.necesita_refrescar_channel_status(
                self.trackers_campana):
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
                # Reiniciamos para ver si se actualizan trackers y status
                continue

            # Si se ha alcanzado el limite global de campañas, tampoco tiene
            # sentido hacer un busy wait
            # +----------------------------------------------------------------
            # | Los eventos que deberian despertar este 'sleep' son:
            # | 1. se ha liberado un canal
            # +----------------------------------------------------------------

            # ATENCION: esta misma logica (o muy parecida) se usa en el loop
            if self._asterisk_call_status.get_count_llamadas() >= \
                settings.FTS_LIMITE_GLOBAL_DE_CANALES:
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

            # Trabajamos en copia, por si hace falta modificarse
            dict_copy = dict(self.trackers_campana)

            for campana, tracker in dict_copy.iteritems():

                # Si la campana esta al limite, la ignoramos
                if tracker.limite_alcanzado():
                    logger.debug("Ignorando campana %s porque esta al limite",
                        campana.id)
                    loop__limite_de_campana_alcanzado = True
                    continue

                #==============================================================
                # Chequeamos limite global de llamadas en curso
                #==============================================================

                loop__esperas_por_limite_global = 0
                while self._asterisk_call_status.get_count_llamadas() >= \
                    settings.FTS_LIMITE_GLOBAL_DE_CANALES:
                    # Se alcanzo el limite global. Hacemos un mini-loop
                    loop__esperas_por_limite_global += 1
                    self.onLimiteGlobalDeCanalesAlcanzadoError()
                    self.real_sleep(settings.\
                        FTS_ESPERA_POR_LIMITE_GLOBAL_DE_CANALES)

                    if loop__esperas_por_limite_global >= 5:
                        # mmm, esto es raro, por las dudas, `continue`
                        logger.warn("generator(): luego de %s loops, todavia"
                            "no podemos continuar porque se ha alcanzado"
                            "el limite global de canales. Continuamos "
                            "con campana siguiente",
                            loop__esperas_por_limite_global)
                        continue # pasamos a prox. campana
                        # Lo ideal seria cortar el loop entero, pero no
                        # se puede facilmente desde aca

                #==============================================================
                # Chequeamos limite de llamadas por segundo
                #==============================================================
                time_to_sleep = self._originate_throttler.time_to_sleep()
                if time_to_sleep > 0.0:
                    self.onLimiteDeOriginatePorSegundosError(time_to_sleep)
                    self.real_sleep(time_to_sleep)

                    # TODO: convendria actualizar el status
                    #  para aprovechar este tiempo de espera.
                    #  El tema es que se actualizarían
                    #  los trackers, y todo este algoritmo en
                    #  `for campana, tracker ...` se hizo suponiendo que
                    #  la actualizacion de trackers se hizo ANTES de arrancar,
                    #  por lo tanto, habria que revisar cuidadosamente todo
                    #  este `for ...` antes de implementar la llamada
                    #  a `self.refrescar_channel_status()`
                    #
                    #if time_to_sleep > 1.0 and \
                    #    self.necesita_refrescar_channel_status():
                    #    self.refrescar_channel_status()
                    #

                try:
                    yield tracker.next()
                    loop__contactos_procesados += 1
                except TodosLosContactosPendientesEstanEnCursoError:
                    self.onTodosLosContactosPendientesEstanEnCursoError(
                        campana)
                    loop__TLCPEECE_detectado = True
                except CampanaNoEnEjecucion:
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

            # ----- ANTES, la situacion era:
            # CORNER CASE: solo podria pasar si justo, mientras se
            # procesaban las campañas, cambio la hora y/o el dia
            # ----- AHORA es distinta:
            # Si se detecta 'TodosLosContactosPendientesEstanEnCursoError',
            # o se ignoro campaña porque llegó al límite de llamadas,
            # y hay una sola campaña en ejecucion, entonces puede
            # suceder q' no se haya procesado ningun contacto
            if loop__contactos_procesados == 0:
                causas_ok = any([loop__TLCPEECE_detectado,
                    loop__limite_de_campana_alcanzado])
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

    def run(self, max_loops=0):
        """Inicia el llamador"""
        current_loop = 1
        for campana, id_contacto, numero, cant_intentos in \
            self.rr_tracker.generator():
            logger.debug("Llamador.run(): campana: %s - id_contacto: %s"
                " - numero: %s", campana, id_contacto, numero)

            originate_ok = procesar_contacto(campana, id_contacto, numero,
                cant_intentos)
            self.rr_tracker.originate_throttler.set_originate(originate_ok)

            current_loop += 1
            if max_loops > 0 and current_loop > max_loops:
                logger.info("Llamador.run(): max_loops alcanzado. Exit!")
                return
