# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from django.conf import settings
from django.db import connection
from django.test.testcases import TestCase
from unittest.case import skipUnless
from mock import Mock, create_autospec

from fts_web.tests.utiles import FTSenderBaseTest, default_db_is_postgresql
from fts_web.models import (BaseDatosContacto, Campana, Contacto,
                            DuracionDeLlamada)
from fts_daemon.models import (EventoDeContacto)
from fts_web.services.generador_de_duracion_de_llamadas import (
    GeneradorDeDuracionDeLlamandasService)


class GeneradorDeDuracionDeLlamadasTest(FTSenderBaseTest):
    """
    Unit Test del método generar_duracion_de_llamdas_para_campana() del
    servicio GeneradorDeDuracionDeLlamandasService.
    """

    def _crea_campana_con_eventos(self):
        base_dato_contacto = BaseDatosContacto(pk=1)
        base_dato_contacto.save()

        for ic in range(1, 6):
            contacto = Contacto(pk=ic)
            contacto.datos = '["111000000{0}", "Carlos", "Ilcobich"]'.format(
                ic)
            contacto.bd_contacto = base_dato_contacto
            contacto.save()

        campana = Campana(pk=1)
        campana.nombre = "Test"
        campana.cantidad_canales = 1
        campana.cantidad_intentos = 1
        campana.segundos_ring = 1
        campana.bd_contacto = base_dato_contacto
        campana.save()

        for ie in range(1, 6):
            evento_contacto = EventoDeContacto(pk=ie)
            evento_contacto.campana_id = 1
            evento_contacto.contacto_id = ie
            evento_contacto.evento = 50
            evento_contacto.dato = 1
            evento_contacto.save()
        return campana

    @skipUnless(default_db_is_postgresql(), "Requiere PostgreSql")
    def test_generar_duracion_de_llamdas_para_campana_no_falla(self):
        campana = self._crea_campana_con_eventos()

        for i in range(1, 6):
            sql = """
            INSERT INTO {0}
            (calldate, clid, src, dst, dcontext, channel, dstchannel, lastapp,
             lastdata, duration, billsec, disposition, amaflags, accountcode,
             uniqueid, userfield, peeraccount, linkedid, sequence)
            VALUES
            ('2014-09-26 20:18:26', 1, 1, '{1}-0110000000000000000{1}-1',
             'FTS_local_campana_{2}',
             'Local/120224-0110000000000000000{1}-1@FTS_local_campana_1-00000001',
             'IAX2/asterisk-a-1727', 'Dial', 'IAX2/172.19.1.101/0110000000000000000{1}',
             1, 1, 'ANSWERED', 3, 1411762706.4, 1, 1, 1411762706.3, 1, 5)
            """.format(settings.FTS_NOMBRE_TABLA_CDR, i, campana.id)

            cursor = connection.cursor()
            cursor.execute(sql)

        # -----

        generador_duracion_llamadas = GeneradorDeDuracionDeLlamandasService()
        generador_duracion_llamadas.generar_duracion_de_llamdas_para_campana(
            campana)

        self.assertEqual(DuracionDeLlamada.objects.count(), 5)

        for i in range(1, 6):
            self.assertEqual(
                DuracionDeLlamada.objects.get(pk=i).numero_telefono,
                '0110000000000000000{0}'.format(i))
