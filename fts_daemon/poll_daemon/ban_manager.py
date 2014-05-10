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

    def __init__(self, baneada_hasta, contador=1):
        self.baneada_hasta = baneada_hasta
        self.contador = contador
        self.objeto_baneado = True

    def des_banear(self):
        """Elimina el baneo en el objeto"""
        self.objeto_baneado = False

    def re_banear(self, baneada_hasta):
        """Vuelve a banear el objeto, aumentando el contador"""
        self.objeto_baneado = True
        self.baneada_hasta = baneada_hasta
        self.contador += 1

    def esta_baneado(self):
        """Devuelve True si el objeto esta baneado, sino False"""
        if not self.objeto_baneado:
            return False

        # FIXME: usar TZ-aware datetimes para soportar cambios de TZ
        if datetime.now() < self.baneada_hasta:
            return True
        else:
            return False


class BanManager(object):
    """Gestiona baneo de campañas (en realidad, sirve para cualquier
    objeto hasheable"""

    def __init__(self):
        self.campanas_baneadas = {}
        """Diccionario que mapea campana (key) a instancia de ``Baneo``
        (que contiene el datetime indicando el momento hasta el cual la
        campaña esta baneada mas el contador de baneos"""

    def get_timedelta_baneo(self):
        """Devuelve tiempo por default de baneo"""
        # TODO: usar time.clock() u alternativa
        return timedelta(minutes=1)

    def banear_campana(self, campana_u_objeto):
        """Banea una campana"""
        # TODO: usar time.clock() u alternativa
        # FIXME: usar TZ-aware datetimes para soportar cambios de TZ

        baneada_hasta = datetime.now() + self.get_timedelta_baneo()
        try:
            baneo = self.campanas_baneadas[campana_u_objeto]
            baneo.re_banear(baneada_hasta)
        except KeyError:
            baneo = Baneo(baneada_hasta)
            self.campanas_baneadas[campana_u_objeto] = baneo

    def des_banear(self, campana_u_objeto):
        """Des-banea una campana"""
        try:
            baneo = self.campanas_baneadas[campana_u_objeto]
            baneo.des_banear()
        except KeyError:
            pass

    def get_baneo(self, campana_u_objeto):
        """Devuelve el objeto Baneo, o None si no existe"""
        try:
            return self.campanas_baneadas[campana_u_objeto]
        except KeyError:
            return None

    def esta_baneada(self, campana_u_objeto):
        """Devuelve booleano indicando si la campana esta baneada."""
        # TODO: usar time.clock() u alternativa
        try:
            baneo = self.campanas_baneadas[campana_u_objeto]
        except KeyError:
            # Campaña no existe, asi q' no esta baneada...
            return False

        return baneo.esta_baneado()

    def eliminar(self, campana_u_objeto):
        """Elimina la informacion de una campana (si existe)."""
        self.des_banear(campana_u_objeto)
