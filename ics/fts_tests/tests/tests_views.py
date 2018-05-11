# -*- coding: utf-8 -*-

"""Tests generales"""

from __future__ import unicode_literals

from django.test.testcases import TransactionTestCase
from fts_daemon import fastagi_daemon
from fts_daemon.fastagi_daemon_views import create_regex
from fts_daemon.models import EventoDeContacto
from fts_tests.tests import tests_fastagi_daemon_views
from fts_tests.tests.tests_fastagi_daemon import TwistedReactorMock
from fts_web.tests.utiles import FTSenderBaseTest, \
    FTSenderBaseTransactionTestCase


LOC_CH_INI = EventoDeContacto.EVENTO_ASTERISK_DIALPLAN_LOCAL_CHANNEL_INICIADO
DP_CAMP_INI = EventoDeContacto.EVENTO_ASTERISK_DIALPLAN_CAMPANA_INICIADO
DP_CAMP_FIN = EventoDeContacto.EVENTO_ASTERISK_DIALPLAN_CAMPANA_FINALIZADO
DP_CAMP_ERR_I = EventoDeContacto.EVENTO_ASTERISK_DIALPLAN_CAMPANA_ERR_I
DP_CAMP_ERR_T = EventoDeContacto.EVENTO_ASTERISK_DIALPLAN_CAMPANA_ERR_T
DS_UNKNOWN = EventoDeContacto.EVENTO_ASTERISK_DIALSTATUS_UNKNOWN
OPC_0 = EventoDeContacto.EVENTO_ASTERISK_OPCION_0
OPC_1 = EventoDeContacto.EVENTO_ASTERISK_OPCION_1
OPC_2 = EventoDeContacto.EVENTO_ASTERISK_OPCION_2
OPC_3 = EventoDeContacto.EVENTO_ASTERISK_OPCION_3
OPC_4 = EventoDeContacto.EVENTO_ASTERISK_OPCION_4
OPC_5 = EventoDeContacto.EVENTO_ASTERISK_OPCION_5
OPC_6 = EventoDeContacto.EVENTO_ASTERISK_OPCION_6
OPC_7 = EventoDeContacto.EVENTO_ASTERISK_OPCION_7
OPC_8 = EventoDeContacto.EVENTO_ASTERISK_OPCION_8
OPC_9 = EventoDeContacto.EVENTO_ASTERISK_OPCION_9


class ViewTests(FTSenderBaseTest):

    def setUp(self):
        self.campana = self.crear_campana_activa()
        self.contacto = list(self.campana.bd_contacto.contactos.all())[-1]
        self.regexes = create_regex()
        self.CONN_POOL_MOCK = tests_fastagi_daemon_views.\
            DjConnectionPoolMock()
        self.REACTOR_MOCK = TwistedReactorMock()

    def _insert_via_url(self, url):
        return fastagi_daemon.do_insert(
            self.REACTOR_MOCK,
            self.CONN_POOL_MOCK,
            self.regexes,
            url
        )

    def tests_local_channel_pre_dial(self):
        # {fts_campana_id}/${{FtsDaemonCallId}}/local-channel-pre-dial/)
        count_inicial = EventoDeContacto.objects.count()
        self.assertEquals(
            EventoDeContacto.objects.filter(evento=LOC_CH_INI).count(), 0)
        url = '{0}/{1}/99/local-channel-pre-dial/'.format(
            self.campana.id, self.contacto.id)

        ret = self._insert_via_url(url)

        count_inicial += 1
        self.assertEquals(EventoDeContacto.objects.count(), count_inicial)

        self.assertEquals(
            EventoDeContacto.objects.filter(evento=LOC_CH_INI).count(), 1)

    def tests_local_channel_post_dial(self):
        # {fts_campana_id}/${{FtsDaemonCallId}}/local-channel-post-dial/
        #     dial-status/${{DIALSTATUS}}/)

        count_inicial = EventoDeContacto.objects.count()
        url = '{0}/{1}/99/local-channel-post-dial/' \
            'dial-status/{2}/'.format(self.campana.id, self.contacto.id,
                'BUSY')
        ret = self._insert_via_url(url)

        count_inicial += 1
        self.assertEquals(EventoDeContacto.objects.count(), count_inicial)

    def tests_local_channel_post_dial_status_invalid(self):

        count_inicial = EventoDeContacto.objects.count()
        self.assertEquals(
            EventoDeContacto.objects.filter(evento=DS_UNKNOWN).count(), 0)
        url = '{0}/{1}/99/local-channel-post-dial/' \
            'dial-status/{2}/'.format(self.campana.id, self.contacto.id,
                'some-invalid-status')
        ret = self._insert_via_url(url)

        count_inicial += 1
        self.assertEquals(EventoDeContacto.objects.count(), count_inicial)

        self.assertEquals(
            EventoDeContacto.objects.filter(evento=DS_UNKNOWN).count(), 1)

    def tests_local_channel_post_dial_status_validos(self):
        DIALSTATUS_MAP = EventoDeContacto.DIALSTATUS_MAP
        count_inicial = EventoDeContacto.objects.count()

        for dial_status in DIALSTATUS_MAP:

            self.assertEquals(
                EventoDeContacto.objects.filter(
                    evento=DIALSTATUS_MAP[dial_status]).count(), 0)

            url = '{0}/{1}/99/local-channel-post-dial/' \
                'dial-status/{2}/'.format(self.campana.id, self.contacto.id,
                    dial_status)
            ret = self._insert_via_url(url)

            count_inicial += 1
            self.assertEquals(EventoDeContacto.objects.count(), count_inicial)

            self.assertEquals(
                EventoDeContacto.objects.filter(
                    evento=DIALSTATUS_MAP[dial_status]).count(), 1)

    def tests_inicio(self):
        # {fts_campana_id}/${{FtsDaemonCallId}}/inicio/)
        count_inicial = EventoDeContacto.objects.count()
        self.assertEquals(
            EventoDeContacto.objects.filter(evento=DP_CAMP_INI).count(), 0)
        url = '{0}/{1}/99/inicio/'.format(self.campana.id,
            self.contacto.id)
        ret = self._insert_via_url(url)

        count_inicial += 1
        self.assertEquals(EventoDeContacto.objects.count(), count_inicial)

        self.assertEquals(
            EventoDeContacto.objects.filter(evento=DP_CAMP_INI).count(), 1)

    def tests_fin(self):
        # {fts_campana_id}/${{FtsDaemonCallId}}/fin/)
        count_inicial = EventoDeContacto.objects.count()
        self.assertEquals(
            EventoDeContacto.objects.filter(evento=DP_CAMP_FIN).count(), 0)
        url = '{0}/{1}/99/fin/'.format(self.campana.id,
            self.contacto.id)
        ret = self._insert_via_url(url)

        count_inicial += 1
        self.assertEquals(EventoDeContacto.objects.count(), count_inicial)

        self.assertEquals(
            EventoDeContacto.objects.filter(evento=DP_CAMP_FIN).count(), 1)

    def tests_opcion_repetir(self):
        # {fts_campana_id}/${{FtsDaemonCallId}}/opcion/
        #    {fts_opcion_digito}/{fts_opcion_id}/repetir/)
        count_inicial = EventoDeContacto.objects.count()
        self.assertEquals(
            EventoDeContacto.objects.filter(evento=OPC_7).count(), 0)
        url = '{0}/{1}/99/opcion/{2}/999/repetir/'.format(
            self.campana.id, self.contacto.id, 7)
        ret = self._insert_via_url(url)

        count_inicial += 1
        self.assertEquals(EventoDeContacto.objects.count(), count_inicial)

        self.assertEquals(
            EventoDeContacto.objects.filter(evento=OPC_7).count(), 1)

    def tests_opcion_derivar(self):
        # {fts_campana_id}/${{FtsDaemonCallId}}/opcion/
        #    {fts_opcion_digito}/{fts_opcion_id}/derivar/)
        count_inicial = EventoDeContacto.objects.count()
        self.assertEquals(
            EventoDeContacto.objects.filter(evento=OPC_7).count(), 0)
        url = '{0}/{1}/99/opcion/{2}/999/derivar/'.format(
            self.campana.id, self.contacto.id, 7)
        ret = self._insert_via_url(url)

        count_inicial += 1
        self.assertEquals(EventoDeContacto.objects.count(), count_inicial)

        self.assertEquals(
            EventoDeContacto.objects.filter(evento=OPC_7).count(), 1)

    def tests_opcion_calificar(self):
        # {fts_campana_id}/${{FtsDaemonCallId}}/opcion/
        #    {fts_opcion_digito}/{fts_opcion_id}/calificar/
        #        {fts_calificacion_id}/)
        count_inicial = EventoDeContacto.objects.count()
        self.assertEquals(
            EventoDeContacto.objects.filter(evento=OPC_7).count(), 0)
        url = '{0}/{1}/99/opcion/{2}/999/calificar/888/'.format(
            self.campana.id, self.contacto.id, 7)
        ret = self._insert_via_url(url)

        count_inicial += 1
        self.assertEquals(EventoDeContacto.objects.count(), count_inicial)

        self.assertEquals(
            EventoDeContacto.objects.filter(evento=OPC_7).count(), 1)

    def tests_opcion_voicemail(self):
        # {fts_campana_id}/${{FtsDaemonCallId}}/opcion/
        #    {fts_opcion_digito}/{fts_opcion_id}/voicemail/)
        count_inicial = EventoDeContacto.objects.count()
        self.assertEquals(
            EventoDeContacto.objects.filter(evento=OPC_7).count(), 0)
        url = '{0}/{1}/99/opcion/{2}/voicemail/'.format(
            self.campana.id, self.contacto.id, 7)
        ret = self._insert_via_url(url)

        count_inicial += 1
        self.assertEquals(EventoDeContacto.objects.count(), count_inicial)

        self.assertEquals(
            EventoDeContacto.objects.filter(evento=OPC_7).count(), 1)

    def tests_opcion_invalida(self):
        count_inicial = EventoDeContacto.objects.count()
        url = '{0}/{1}/99/opcion/{2}/voicemail/'.format(
            self.campana.id, self.contacto.id, "10")
        ret = self._insert_via_url(url)

        self.assertEquals(EventoDeContacto.objects.count(), count_inicial)

    def tests_opciones_validas(self):
        op_evento = (
            (0, OPC_0),
            (1, OPC_1),
            (2, OPC_2),
            (3, OPC_3),
            (4, OPC_4),
            (5, OPC_5),
            (6, OPC_6),
            (7, OPC_7),
            (8, OPC_8),
            (9, OPC_9),
        )

        count_inicial = EventoDeContacto.objects.count()
        for op, evento in op_evento:
            self.assertEquals(
                EventoDeContacto.objects.filter(evento=evento).count(), 0)
            url = '{0}/{1}/99/opcion/{2}/voicemail/'.format(
                self.campana.id, self.contacto.id, op)
            ret = self._insert_via_url(url)

            count_inicial += 1
            self.assertEquals(EventoDeContacto.objects.count(), count_inicial)

            self.assertEquals(
                EventoDeContacto.objects.filter(evento=evento).count(), 1)

    def tests_err_t(self):
        # {fts_campana_id}/${{FtsDaemonCallId}}/fin_err_t/)
        count_inicial = EventoDeContacto.objects.count()
        self.assertEquals(
            EventoDeContacto.objects.filter(evento=DP_CAMP_ERR_T).count(), 0)

        url = '{0}/{1}/99/fin_err_t/'.format(self.campana.id,
            self.contacto.id)
        ret = self._insert_via_url(url)

        count_inicial += 1
        self.assertEquals(EventoDeContacto.objects.count(), count_inicial)

        self.assertEquals(
            EventoDeContacto.objects.filter(evento=DP_CAMP_ERR_T).count(), 1)

    def tests_err_i(self):
        # {fts_campana_id}/${{FtsDaemonCallId}}/fin_err_i/)
        count_inicial = EventoDeContacto.objects.count()
        self.assertEquals(
            EventoDeContacto.objects.filter(evento=DP_CAMP_ERR_I).count(), 0)
        url = '{0}/{1}/99/fin_err_i/'.format(self.campana.id,
            self.contacto.id)
        ret = self._insert_via_url(url)

        count_inicial += 1
        self.assertEquals(EventoDeContacto.objects.count(), count_inicial)
        self.assertEquals(
            EventoDeContacto.objects.filter(evento=DP_CAMP_ERR_I).count(), 1)
