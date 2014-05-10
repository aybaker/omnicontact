# -*- coding: utf-8 -*-
"""

"""

from __future__ import unicode_literals

from datetime import datetime, timedelta


class BanManager(object):
    """Gestiona baneo de campañas (en realidad, sirve para cualquier
    objeto hasheable"""

    def __init__(self):
        self.campanas_baneadas = {}
        """Diccionario que mapea campana (key) al datetime indicando el
        momento hasta el cual la campaña esta baneada"""

    def get_timedelta_baneo(self):
        """Devuelve tiempo por default de baneo"""
        # TODO: usar time.clock() u alternativa
        return timedelta(minutes=1)

    def banear_campana(self, campana_u_objeto):
        """Banea una campana"""
        # TODO: usar time.clock() u alternativa
        self.campanas_baneadas[campana_u_objeto] = datetime.now() + \
            self.get_timedelta_baneo()

    def esta_baneada(self, campana_u_objeto):
        """Devuelve booleano indicando si la campana esta baneada.
        """
        # TODO: usar time.clock() u alternativa
        try:
            baneada_hasta = self.campanas_baneadas[campana_u_objeto]
        except KeyError:
            # Campaña no existe, asi q' no esta baneada...
            return False

        # Existe! Chequeamos si todavia está vigente
        if datetime.now() < baneada_hasta:
            return True
        else:
            del self.campanas_baneadas[campana_u_objeto]
            return False

    def eliminar(self, campana_u_objeto):
        """Elimina la informacion de una campana (si existe)."""
        try:
            del self.campanas_baneadas[campana_u_objeto]
        except KeyError:
            return False
