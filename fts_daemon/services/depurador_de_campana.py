# -*- coding: utf-8 -*-
"""
Servicio que realiza todos los pasos necesarios para la depuración
de una Campaña finalizada, incluyendo:
- Recalculo de Agregación de EDC
- Creación de reporte
- Depuración de EDC
"""

from __future__ import unicode_literals

from django.db import transaction
from fts_daemon.models import EventoDeContacto
from fts_web.models import Campana
import logging as _logging


logger = _logging.getLogger(__name__)


class CampanaNoPuedeDepurarseError(Exception):
    pass


class DepuradorDeCampanaWorkflow(object):
    """Implementa los pasos necesarios para depurar la campaña."""

    def _obtener_campana(self, campana_id):
        return Campana.objects.get(pk=campana_id)

    def _depurar(self, campana):
        if not campana.puede_depurarse():
            logger.error("La campaña %s NO esta en condiciones de "
                         "ser depurada", campana.id)
            raise(CampanaNoPuedeDepurarseError("La campana no esta en "
                                               "condiciones de ser depurada"))

        # Recalcula agregacion
        campana.recalcular_aedc_completamente()

        # Genera reporte CSV
        campana.crea_reporte_csv()

        # Depura EDC
        EventoDeContacto.objects.depurar_eventos_de_contacto(campana.id)

        # Setea la campaña como depurada
        campana.depurar()

        return True

    def depurar(self, campana_id):
        """Realiza depuración. Devuelve True si la campaña se depuro.
        False si no hizo falta depurarla porque la campaña ya estaba depurada.

        :raises CampanaNoPuedeDepurarseError: si el estado de la campaña no
                                              permite su depuracion.
        """
        logger.info("Se iniciara el proceso de depuracion para la camana %s",
                    campana_id)

        with transaction.atomic():
            campana = self._obtener_campana(campana_id)
            if campana.estado == Campana.ESTADO_DEPURADA:
                logger.info("Ignorando campana ya depurada: %s", campana.id)
                return False
            self._depurar(campana)

        # Fuera de la TX, logueamos OK (por si se produce un error
        # al realizar commit)
        logger.info("La campana %s fue finalizada correctamente", campana_id)
        return True
