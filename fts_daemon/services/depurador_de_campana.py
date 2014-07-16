# -*- coding: utf-8 -*-
"""
Componentes encargados del finalizado de Campañas.
"""

from __future__ import unicode_literals

from django.db import transaction
from fts_daemon.models import EventoDeContacto
from fts_web.models import Campana
import logging as _logging


logger = _logging.getLogger(__name__)


class DepuradorDeCampanaWorkflow(object):
    """Realiza los chequeos y pasos necesarios para finalizar una campaña.
    El metodo `finalizar()` debe ser llamddo, y pasar el ID de la campaña
    a finalizar por parametro."""

    def _obtener_campana(self, campana_id):
        return Campana.objects.get(pk=campana_id)

    def _finalizar(self, campana):
        # assert isinstance(campana, Campana)
        assert campana.puede_finalizarse()

        campana.recalcular_aedc_completamente()
        campana.finalizar()

        # campana.procesar_finalizada()
        campana.crea_reporte_csv()
        EventoDeContacto.objects.depurar_eventos_de_contacto(campana.id)

    def finalizar(self, campana_id):
        logger.info("Se iniciara el proceso de finalizacion para la camana %s",
                    campana_id)

        with transaction.atomic():

            campana = self._obtener_campana(campana_id)
            if campana.estado == Campana.ESTADO_FINALIZADA:
                logger.info("Ignorando campana ya finalizada: %s", campana_id)
                return

            self._finalizar(campana)

        # Fuera de la TX, logueamos OK (por si se produce un error
        # al realizar commit)
        logger.info("La campana %s fue finalizada correctamente",
                    campana_id)
