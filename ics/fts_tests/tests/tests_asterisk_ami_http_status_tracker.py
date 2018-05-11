# -*- coding: utf-8 -*-

"""Tests del modulo fts_daemon.asterisk_status"""

from __future__ import unicode_literals

from django.conf import settings
from django.test.testcases import LiveServerTestCase
from django.test.utils import override_settings
from fts_daemon.asterisk_ami_http import AmiStatusTracker
import logging as _logging


logger = _logging.getLogger(__name__)


class AmiStatusTrackerTestUtilesMixin():

    def assertStatusEqual(self, dict1, dict2):
        # return self.assertDictEqual(dict1, dict2)
        # Igual tamaño
        self.assertEqual(len(dict1), len(dict2))
        # Iguales keys
        self.assertListEqual(
            sorted([x for x in dict1]),
            sorted([x for x in dict2]),
        )
        # Iguales valores
        for k in dict1:
            self.assertEqual(
                sorted(dict1[k]),
                sorted(dict2[k])
            )

    def _code(self, code):
        asterisk = settings.ASTERISK
        asterisk['HTTP_AMI_URL'] = self.live_server_url + \
            "/asterisk-ami-http/" + code
        return asterisk


class AmiStatusTrackerTest(LiveServerTestCase,
    AmiStatusTrackerTestUtilesMixin):

    def test_con_local_channel(self):
        sett = self._code('status-con-local-channel')
        with override_settings(HTTP_AMI_URL=sett):
            status_tracker = AmiStatusTracker()
            status = status_tracker.get_status_por_campana()
        self.assertDictEqual(status, {78: [[2922816, '6500', 78, 1]]})

    def test_con_llamada_en_no_local_channel(self):
        """Testea que tiene en cuenta llamadas en curso que no poseen
        el LocalChannel activo.

        Esta situacion se detecto en el 4to sprint. Al parecer, Asterisk
        cierra el LocalChannel (cuando la llamada ya esta "en curso", en el
        contexto de la campana).
        """
        #
        # context='campania_156'
        # extension='fts-2933997-1000000001-1'
        #
        sett = self._code('status-con-1-llamada-en-channel-no-local')
        with override_settings(HTTP_AMI_URL=sett):
            status_tracker = AmiStatusTracker()
            status = status_tracker.get_status_por_campana()
        self.assertDictEqual(status, {156:
            [[2933997, u'1000000001', 156, 1]]})

    def test_sin_llamadas(self):
        sett = self._code('status-sin-llamadas')
        with override_settings(HTTP_AMI_URL=sett):
            status_tracker = AmiStatusTracker()
            status = status_tracker.get_status_por_campana()
        self.assertDictEqual(status, {})

    def test_local_channel_ringing(self):
        sett = self._code('status-muchas-1-llamada-en-local-channel-ringing')
        with override_settings(HTTP_AMI_URL=sett):
            status_tracker = AmiStatusTracker()
            status = status_tracker.get_status_por_campana()
        self.assertDictEqual(status, {86:
            [[2923389, u'319751355727335', 86, 1]]})

    def test_con_muchas_llamadas(self):
        sett = self._code('status-muchas-llamadas')
        with override_settings(HTTP_AMI_URL=sett):
            status_tracker = AmiStatusTracker()
            status = status_tracker.get_status_por_campana()
        res = {80: [
            [2922884, u'671', 80, 1],
            [2922897, u'684', 80, 1],
            [2922989, u'681', 80, 1],
            [2922868, u'655', 80, 1],
            [2922898, u'685', 80, 1],
            [2922903, u'690', 80, 1],
            [2922990, u'682', 80, 1],
            [2922900, u'687', 80, 1],
            [2922972, u'664', 80, 1],
            [2923003, u'695', 80, 1],
            [2922980, u'672', 80, 1],
            [2922901, u'688', 80, 1],
            [2922873, u'660', 80, 1],
            [2922960, u'652', 80, 1],
            [2922885, u'672', 80, 1],
            [2922957, u'649', 80, 1],
            [2922876, u'663', 80, 1],
            [2922909, u'696', 80, 1],
            [2922977, u'669', 80, 1],
            [2922904, u'691', 80, 1],
            [2922866, u'653', 80, 1],
            [2922911, u'698', 80, 1],
            [2922961, u'653', 80, 1],
            [2922973, u'665', 80, 1],
            [2922971, u'663', 80, 1],
            [2922958, u'650', 80, 1],
            [2922959, u'651', 80, 1],
            [2922871, u'658', 80, 1],
            [2922878, u'665', 80, 1],
            [2922880, u'667', 80, 1],
            [2922867, u'654', 80, 1],
            [2922992, u'684', 80, 1],
            [2922983, u'675', 80, 1],
            [2922889, u'676', 80, 1],
            [2922956, u'648', 80, 1],
            [2922902, u'689', 80, 1],
            [2922861, u'648', 80, 1],
            [2922987, u'679', 80, 1],
            [2922893, u'680', 80, 1],
            [2922998, u'690', 80, 1],
            [2922981, u'673', 80, 1],
            [2923002, u'694', 80, 1],
            [2922907, u'694', 80, 1],
            [2922912, u'699', 80, 1],
        ]}

        self.assertStatusEqual(status, res)

        sett = self._code('status-muchas-llamadas-4-campanas')
        with override_settings(HTTP_AMI_URL=sett):
            status_tracker = AmiStatusTracker()
            status = status_tracker.get_status_por_campana()

        res = {
            81: [
                [2923030, u'627', 81, 1],
                [2923018, u'615', 81, 1],
                [2923055, u'652', 81, 1],
                [2923064, u'661', 81, 1],
                [2923015, u'612', 81, 1],
                [2923014, u'611', 81, 1],
                [2923034, u'631', 81, 1],
                [2923031, u'628', 81, 1],
                [2923019, u'616', 81, 1],
                [2923027, u'624', 81, 1],
                [2923029, u'626', 81, 1],
                [2923023, u'620', 81, 1],
                [2923017, u'614', 81, 1],
                [2923028, u'625', 81, 1],
                [2923021, u'618', 81, 1],
                [2923012, u'609', 81, 1],
                [2923022, u'619', 81, 1],
                [2923033, u'630', 81, 1],
                [2923020, u'617', 81, 1],
                [2923032, u'629', 81, 1],
                [2923026, u'623', 81, 1],
                [2923025, u'622', 81, 1],
                [2923016, u'613', 81, 1]],
            82: [
                [2923112, u'614', 82, 1],
                [2923109, u'611', 82, 1],
                [2923137, u'639', 82, 1],
                [2923172, u'674', 82, 1],
                [2923125, u'627', 82, 1],
                [2923160, u'662', 82, 1],
                [2923154, u'656', 82, 1],
                [2923108, u'610', 82, 1],
                [2923111, u'613', 82, 1],
                [2923143, u'645', 82, 1],
                [2923167, u'669', 82, 1],
                [2923133, u'635', 82, 1],
                [2923149, u'651', 82, 1],
                [2923118, u'620', 82, 1],
                [2923142, u'644', 82, 1],
                [2923165, u'667', 82, 1],
                [2923115, u'617', 82, 1],
                [2923147, u'649', 82, 1],
                [2923145, u'647', 82, 1],
                [2923157, u'659', 82, 1],
                [2923121, u'623', 82, 1],
                [2923164, u'666', 82, 1],
                [2923130, u'632', 82, 1],
                [2923123, u'625', 82, 1],
                [2923159, u'661', 82, 1],
                [2923140, u'642', 82, 1]],
            83: [
                [2923227, u'634', 83, 1],
                [2923222, u'629', 83, 1],
                [2923230, u'637', 83, 1],
                [2923253, u'660', 83, 1],
                [2923239, u'646', 83, 1],
                [2923238, u'645', 83, 1],
                [2923237, u'644', 83, 1],
                [2923234, u'641', 83, 1],
                [2923219, u'626', 83, 1],
                [2923233, u'640', 83, 1],
                [2923236, u'643', 83, 1],
                [2923262, u'669', 83, 1],
                [2923210, u'617', 83, 1],
                [2923288, u'695', 83, 1],
                [2923249, u'656', 83, 1],
                [2923241, u'648', 83, 1],
                [2923226, u'633', 83, 1],
                [2923247, u'654', 83, 1],
                [2923263, u'670', 83, 1],
                [2923257, u'664', 83, 1],
                [2923207, u'614', 83, 1],
                [2923218, u'625', 83, 1],
                [2923255, u'662', 83, 1],
                [2923220, u'627', 83, 1],
                [2923232, u'639', 83, 1],
                [2923256, u'663', 83, 1],
                [2923229, u'636', 83, 1]],
            84: [
                [2923302, u'614', 84, 1],
                [2923324, u'636', 84, 1],
                [2923310, u'622', 84, 1],
                [2923303, u'615', 84, 1],
                [2923328, u'640', 84, 1],
                [2923335, u'647', 84, 1],
                [2923298, u'610', 84, 1],
                [2923304, u'616', 84, 1],
                [2923316, u'628', 84, 1],
                [2923321, u'633', 84, 1],
                [2923323, u'635', 84, 1],
                [2923329, u'641', 84, 1],
                [2923305, u'617', 84, 1],
                [2923299, u'611', 84, 1],
                [2923313, u'625', 84, 1],
                [2923301, u'613', 84, 1],
                [2923332, u'644', 84, 1],
                [2923346, u'658', 84, 1],
                [2923300, u'612', 84, 1],
                [2923315, u'627', 84, 1],
                [2923317, u'629', 84, 1],
                [2923311, u'623', 84, 1],
                [2923322, u'634', 84, 1],
                [2923320, u'632', 84, 1],
                [2923325, u'637', 84, 1],
                [2923371, u'683', 84, 1]
        ]}

        self.assertStatusEqual(status, res)


class CustomStatusViewTest(LiveServerTestCase,
    AmiStatusTrackerTestUtilesMixin):

    def test_custom_status(self):
        status_tracker = AmiStatusTracker()

        # ----- simple -----
        custom_status_values = [
            [1234, 9876, "01140008000", 777]
        ]

        with override_settings(
            HTTP_AMI_URL=self._code('status-llamada-en-local-channel-CUSTOM'),
            CUSTOM_STATUS_VALUES=custom_status_values):

            status = status_tracker.get_status_por_campana()

        res = {
            1234: [
                [9876, "01140008000", 1234, 777],
            ]
        }

        self.assertStatusEqual(status, res)

        # ----- mas complejo -----
        custom_status_values = [
            [1234, 9876, "01140008000", 1],
            [1234, 9898, "01140008001", 3],
            [1234, 9888, "01140008002", 1],
            [1934, 4876, "03514008006", 9],
            [1934, 4898, "03514008007", 8],
            [1934, 4989, "03514008008", 7],
        ]

        with override_settings(
            HTTP_AMI_URL=self._code('status-llamada-en-local-channel-CUSTOM'),
            CUSTOM_STATUS_VALUES=custom_status_values):

            status = status_tracker.get_status_por_campana()

        res = {
            1234: [
                [9876, "01140008000", 1234, 1],
                [9898, "01140008001", 1234, 3],
                [9888, "01140008002", 1234, 1],
            ],
            1934: [
                [4876, "03514008006", 1934, 9],
                [4898, "03514008007", 1934, 8],
                [4989, "03514008008", 1934, 7],
            ],
        }

        self.assertStatusEqual(status, res)
