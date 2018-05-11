# -*- coding: utf-8 -*-
"""

"""

from __future__ import unicode_literals

from datetime import datetime, timedelta

from django.conf import settings
from fts_daemon.asterisk_ami_http import AmiStatusTracker
from fts_daemon.poll_daemon.ban_manager import BanManager
from fts_daemon.poll_daemon.campana_tracker import CampanaTracker
from fts_web.models import Campana
import logging as _logging


logger = _logging.getLogger(__name__)


class NoHayCampanaEnEjecucion(Exception):
    """No se encontraron campanas en ejecucion. O si hay campañas,
    estan baneadas.
    """


class CampanaCallStatus(object):
    """Traquea el status de todas las campañas en conjunto."""

    def __init__(self):
        """Constructor"""

        self._trackers_campana_dict = {}
        """Diccionario con los trackers de las campañas, ya sea que
        estan siendo procesadas, o baneadas.

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
        """Banea la campana pasada por parametro"""
        return self._ban_manager.banear_campana(campana_u_objeto,
            reason=reason, forever=forever)

    def obtener_baneados_por_razon(self, reason):
        return self._ban_manager.obtener_por_razon(reason)

    def _obtener_campanas_en_ejecucion(self):
        """Devuelve campañas en ejecucion. Las busca en la BD"""
        return Campana.objects.obtener_ejecucion()

    def _get_tiempo_minimo_entre_refresco(self):
        """Devuelve float que representa el tiempo minimo (en segundos)
        que debe pasar entre refrescos"""
        # FIXME: mover a settings
        return 10.0

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
        # TODO: deberia llamarse 'puede_refrescar_trackers()'

        # Quizá habria q' chequear más seguido si el server no
        # está haciendo nada, pero más espaciado si hay
        # llamadas en curso, no?

        # TODO: usar time.clock() u alternativa
        delta = datetime.now() - self._ultimo_refresco_trackers
        if delta.days > 0:
            return True

        elapsed = float(delta.seconds) + (float(delta.microseconds) / 1e6)
        if elapsed > self._get_tiempo_minimo_entre_refresco():
            return True

        return False

    def _crear_tracker(self, campana=None, campana_id=None):
        """Instancia CampanaTracker para la campaña pasada por parametro
        y la devuelve."""
        assert campana is not None or campana_id is not None, \
            "debe especificarse campana o campana_id (ambos son None)"
        assert campana is None or campana_id is None, \
            "solo debe especificarse campana o campana_id, no ambas"

        if campana is not None:
            return CampanaTracker(campana)

        if campana_id is not None:
            campana = Campana.objects.get(pk=campana_id)
            return CampanaTracker(campana)

        assert False, "No debio llegarse aqui"

    def refrescar_trackers_activos(self):
        """Revisa si algun tracker activo fue baneado, y actualiza trackers.

        Los tracker no-activos que sean des-baneado (o sea, se les vence
        el baneo), NO son tenidos en cuenta.

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
                    current_trackers[campana] = self._crear_tracker(campana)
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
            current_trackers[campana] = self._crear_tracker(campana)

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
        ACTIVAS/en curso estan al limite"""
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
                # Si necesita refrescar trackers, los refresca
                self.refrescar_trackers()  # -> NoHayCampanaEnEjecucion
            else:
                # Si no necesita refrescar trackers, debemos refrescar
                # los activos, por si hubo baneos
                self.refrescar_trackers_activos()  # -> NoHayCampanaEnEjecucion
        except NoHayCampanaEnEjecucion:
            # Cualquiera de los 2 metodos de arriba pueden detectar q' no hay
            # campañas en ejecucion.
            self.onNoHayCampanaEnEjecucion()

        return list(self._trackers_activos)

    @property
    def trackers_activos(self):
        """Devuelve lista de trackers activos. NO intenta actualizar.
        Si hace falta intentar actualizar, usar
        `obtener_trackers_para_procesar()`
        """
        return list(self._trackers_activos)

    @property
    def count_trackers_activos(self):
        """Devuelve cantidad de trackers activos."""
        return len(self._trackers_activos)

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

        for campana_id, items in full_status.iteritems():
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

            tracker = self._crear_tracker(campana_id=campana_id)
            tracker.contactos_en_curso = contactos
            tracker.desactivar()
            campana = tracker.campana
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

    def get_count_llamadas_de_campana(self, campana):
        """Devuelve el count total (APROXIMADO) de llamadas en curso
        para la campaña pasada por parametro.
        """
        try:
            tracker = self._trackers_campana_dict[campana]
        except KeyError:
            return 0

        return tracker.llamadas_en_curso_aprox

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
        """Si puede refrescar, refresca.

        :returns: bool - True si se refresco. False si no.
        """
        if self.puede_refrescar():
            return self.refrescar_channel_status()
        return False

    def _get_status_por_campana(self):
        return self._ami_status_tracker.get_status_por_campana()

    def refrescar_channel_status(self):
        """Refresca `contactos_en_curso` de `self.trackers_campana`.

        En caso de error, no actualiza ningun valor.

        :returns: bool - True si se refresco. False si no.
        """
        # Antes q' nada, actualizamos 'ultimo refresco'
        self.touch()

        logger.info("refrescar_channel_status(): obteniendo status...")
        try:
            full_status = self._get_status_por_campana()
        except:
            # FIXME: esta excepcion deberia propagarse!
            logger.exception("Error detectado al ejecutar "
                "ami_status_tracker.get_status_por_campana(). Los statuses "
                "no seran actualizados")
            return False

        # Actualizamos trackers
        self._campana_call_status.update_call_status(full_status)
        return True
