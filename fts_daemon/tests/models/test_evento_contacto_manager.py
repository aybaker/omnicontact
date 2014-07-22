# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import datetime
import os

from django.test.utils import override_settings

from fts_web.models import Campana
from django.db.utils import ProgrammingError
from django.db import connection
from fts_web.tests.utiles import FTSenderBaseTest
from fts_daemon.models import EventoDeContacto
from fts_daemon.services.depurador_de_campana import DepuradorDeCampanaWorkflow
from mock import Mock, patch


class DepurarEventosDeContactoTest(FTSenderBaseTest):

    def test_eliminar_tabla_eventos_de_contacto_depurada(self):
        campana = self.crear_campana_finalizada()

        nombre_tabla = "EDC_depurados_{0}".format(campana.pk)

        cursor = connection.cursor()
        sql = """CREATE TABLE {0} AS
            SELECT * FROM fts_daemon_eventodecontacto
            WHERE campana_id = %s
            WITH DATA
        """.format(nombre_tabla)

        params = [campana.id]
        cursor.execute(sql, params)

        def check_tabla():
            sql = "SELECT * FROM {0} LIMIT 1".format(nombre_tabla)
            cursor.execute(sql)

        check_tabla()

        # -----

        EventoDeContacto.objects.eliminar_tabla_eventos_de_contacto_depurada(
            campana.pk)

        with self.assertRaises(ProgrammingError):
            check_tabla()
