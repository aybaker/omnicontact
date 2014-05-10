# -*- coding: utf-8 -*-
"""

"""

from __future__ import unicode_literals

from datetime import datetime, timedelta

# FIXME: usar TZ-aware datetimes para soportar cambios de TZ


class Baneo(object):
    """Representa un objeto baneado (alguna vez). Actualmente, puede
    representar a un objeto baneado o no
    """

    def __init__(self, baneada_hasta, contador=1, reason=None):
        assert type(baneada_hasta) == datetime
        assert type(contador) == int
        self._baneada_hasta = baneada_hasta
        self._contador = contador
        self._objeto_esta_baneado = True
        self._reason = reason

    @property
    def contador(self):
        return self._contador

    @property
    def objeto_esta_baneado(self):
        return self._objeto_esta_baneado

    @property
    def reason(self):
        return self._reason

    @property
    def baneada_hasta(self):
        return self._baneada_hasta

    def des_banear(self):
        """Elimina el baneo en el objeto"""
        self._objeto_esta_baneado = False

    def re_banear(self, baneada_hasta, reason=None):
        """Vuelve a banear el objeto, aumentando el contador"""
        assert type(baneada_hasta) == datetime
        self._objeto_esta_baneado = True
        self._baneada_hasta = baneada_hasta
        self._contador += 1
        if reason is not None:
            self._reason = reason

    def esta_baneado(self):
        """Devuelve True si el objeto esta baneado, sino False"""
        if not self._objeto_esta_baneado:
            return False

        # FIXME: usar TZ-aware datetimes para soportar cambios de TZ
        if datetime.now() < self._baneada_hasta:
            return True
        else:
            return False


class BanManager(object):
    """Gestiona baneo de campañas (en realidad, sirve para cualquier
    objeto hasheable"""

    def __init__(self):
        self._campanas_baneadas = {}
        """Diccionario que mapea campana (key) a instancia de ``Baneo``
        (que contiene el datetime indicando el momento hasta el cual la
        campaña esta baneada mas el contador de baneos"""

    @property
    def campanas_baneadas(self):
        # Devolvemos copia
        return dict(self._campanas_baneadas)

    def get_timedelta_baneo(self):
        """Devuelve tiempo por default de baneo"""
        # TODO: usar time.clock() u alternativa
        return timedelta(minutes=1)

    def banear_campana(self, campana_u_objeto, reason=None):
        """Banea (o re-banea)  una campana"""
        # TODO: usar time.clock() u alternativa
        # FIXME: usar TZ-aware datetimes para soportar cambios de TZ

        baneada_hasta = datetime.now() + self.get_timedelta_baneo()
        try:
            baneo = self._campanas_baneadas[campana_u_objeto]
            baneo.re_banear(baneada_hasta, reason)
        except KeyError:
            baneo = Baneo(baneada_hasta, reason=reason)
            self._campanas_baneadas[campana_u_objeto] = baneo

    def des_banear(self, campana_u_objeto):
        """Des-banea una campana"""
        try:
            baneo = self._campanas_baneadas[campana_u_objeto]
            baneo.des_banear()
        except KeyError:
            pass

    def get_baneo(self, campana_u_objeto):
        """Devuelve el objeto Baneo, o None si no existe"""
        try:
            return self._campanas_baneadas[campana_u_objeto]
        except KeyError:
            return None

    def esta_baneada(self, campana_u_objeto):
        """Devuelve booleano indicando si la campana esta baneada."""
        # TODO: usar time.clock() u alternativa
        try:
            baneo = self._campanas_baneadas[campana_u_objeto]
        except KeyError:
            # Campaña no existe, asi q' no esta baneada...
            return False

        return baneo.esta_baneado()

#    def eliminar(self, campana_u_objeto):
#        """Elimina la informacion de una campana (si existe)."""
#        try:
#            del self._campanas_baneadas[campana_u_objeto]
#        except KeyError:
#            pass
