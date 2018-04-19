# -*- coding: utf-8 -*-

"""Tests del modulo fts_daemon.asterisk_status"""

from __future__ import unicode_literals

import os
import pprint
import uuid
import unittest

from django.conf import settings
from django.test.testcases import LiveServerTestCase
from django.test.utils import override_settings
from fts_daemon.asterisk_ami_http import AsteriskHttpClient, \
    AsteriskHttpAuthenticationFailedError, \
    AsteriskHttpResponseWithError, get_response_on_first_element, \
    AsteriskXmlParserForStatus, AsteriskHttpOriginateError
from fts_web.tests.utiles import FTSenderBaseTest
import logging as _logging
import xml.etree.ElementTree as ET


logger = _logging.getLogger(__name__)


class TestAsteriskXmlParserForStatus(FTSenderBaseTest):

    def test_con_1_llamada(self):
        parser = AsteriskXmlParserForStatus()
        parser.parse(self.read_test_resource("mxml-status-con-1-llamada.xml"))
        for call_dict in parser.calls_dicts:
            if 'context' in call_dict:
                logger.debug("Channel: %s - Context: %s - Exten: %s - "
                    "CallId: %s - BidgedChan: %s",
                    call_dict['channel'],
                    call_dict['context'],
                    call_dict['extension'],
                    call_dict['calleridnum'],
                    call_dict['bridgedchannel'],
                )
            else:
                logger.debug("CallDict: %s", call_dict)

    def test_sin_llamadas(self):
        parser = AsteriskXmlParserForStatus()
        parser.parse(self.read_test_resource("mxml-status-sin-llamados.xml"))

    def test_ringing(self):
        parser = AsteriskXmlParserForStatus()
        parser.parse(self.read_test_resource("mxml-status-ringing.xml"))


class TestAsteriskXmlParser(FTSenderBaseTest):

    def test_get_response_on_first_element(self):

        ret = get_response_on_first_element(
            ET.fromstring(self.read_test_resource(
                "mxml-permission-denied.xml")))
        self.assertDictEqual(ret, {
            'response': 'Error',
            'message': 'Permission denied',
        })

        ret = get_response_on_first_element(
            ET.fromstring(self.read_test_resource(
                "mxml-login-success-authentication-accepted.xml")))
        self.assertDictEqual(ret, {
            'response': 'Success',
            'message': 'Authentication accepted',
        })

        ret = get_response_on_first_element(
            ET.fromstring(self.read_test_resource(
                "mxml-status-con-1-llamada.xml")))
        self.assertDictEqual(ret, {
            'response': 'Success',
            'message': 'Channel status will follow',
        })

        ret = get_response_on_first_element(
            ET.fromstring(self.read_test_resource(
                "mxml-status-sin-llamados.xml")))
        self.assertDictEqual(ret, {
            'response': 'Success',
            'message': 'Channel status will follow',
        })

        ret = get_response_on_first_element(
            ET.fromstring(self.read_test_resource(
                "mxml-status-ringing.xml")))
        self.assertDictEqual(ret, {
            'response': 'Success',
            'message': 'Channel status will follow',
        })


class TestBasicosUtil(LiveServerTestCase):

    def _code(self, code):
        asterisk = settings.ASTERISK
        asterisk['HTTP_AMI_URL'] = self.live_server_url + \
            "/asterisk-ami-http/" + code
        return asterisk

    def test_login(self):
        client = AsteriskHttpClient()
        with override_settings(HTTP_AMI_URL=self._code('login-ok')):
            client.login()

    def test_ping(self):
        client = AsteriskHttpClient()
        with override_settings(HTTP_AMI_URL=self._code('ping-ok')):
            client.ping()

    def test_status(self):
        client = AsteriskHttpClient()

        sett = self._code('status-con-local-channel')
        with override_settings(HTTP_AMI_URL=sett):
            client.get_status()

        sett = self._code('status-1-llamada')
        with override_settings(HTTP_AMI_URL=sett):
            client.get_status()

        sett = self._code('status-sin-llamadas')
        with override_settings(HTTP_AMI_URL=sett):
            client.get_status()

        sett = self._code('status-ringing')
        with override_settings(HTTP_AMI_URL=sett):
            client.get_status()

        sett = self._code('status-muchas-1-llamada-en-local-channel-ringing')
        with override_settings(HTTP_AMI_URL=sett):
            client.get_status()

    def test_auth_failed(self):
        client = AsteriskHttpClient()
        sett = self._code('login-auth-failed')
        with override_settings(HTTP_AMI_URL=sett):
            with self.assertRaises(AsteriskHttpAuthenticationFailedError):
                client.login()

    def test_perm_denied(self):
        client = AsteriskHttpClient()
        sett = self._code('permission-denied')

        with override_settings(HTTP_AMI_URL=sett):
            with self.assertRaises(AsteriskHttpResponseWithError):
                client.ping()

        with override_settings(HTTP_AMI_URL=sett):
            with self.assertRaises(AsteriskHttpResponseWithError):
                client.get_status()

    def test_originate(self):
        client = AsteriskHttpClient()

        sett = self._code('originate-ok')
        with override_settings(HTTP_AMI_URL=sett):
            client.originate("IAX2/xx.xx.xx.xx/010101010101",
            "xxxxxx", "100", "1", 10000, True, {})

        sett = self._code('originate-failed')
        with override_settings(HTTP_AMI_URL=sett):
            with self.assertRaises(AsteriskHttpOriginateError):
                client.originate("IAX2/xx.xx.xx.xx/010101010101",
                    "xxxxxx", "100", "1", 10000, True, {})

        sett = self._code('originate-failed-exten-not-exists')
        with override_settings(HTTP_AMI_URL=sett):
            with self.assertRaises(AsteriskHttpOriginateError):
                client.originate("IAX2/xx.xx.xx.xx/010101010101",
                    "xxxxxx", "100", "1", 10000, True, {})


#==============================================================================
# Algunos tests simples q' requieren Asterisk
#==============================================================================

@unittest.skipUnless('FTS_RUN_ASTERISK_TEST' in os.environ,
    "Asterisk tests disabled")
class TestOriginateFailsIfContextDoesntExists(FTSenderBaseTest):

    CHANNEL = "Local/123-100@FTS-dialer-local-C"
    CONTEXT_OK = "from_test_server"
    CONTEXT_DOESN_EXISTS = "non-existing-ctx-{0}".format(uuid.uuid4().hex)
    EXTEN = "100"
    PRIO = "1"
    TIMEOUT = 10000

    def test_asterisk_works(self):
        client = AsteriskHttpClient()
        client.login()
        client.ping()

        client.originate(self.CHANNEL, self.CONTEXT_OK,
            self.EXTEN, self.PRIO, self.TIMEOUT, True, {})

    def test_asterisk_fails(self):
        client = AsteriskHttpClient()
        client.login()
        client.ping()

        with self.assertRaises(AsteriskHttpOriginateError):
            client.originate(self.CHANNEL, self.CONTEXT_DOESN_EXISTS,
                self.EXTEN, self.PRIO, self.TIMEOUT, True, {})


@unittest.skipUnless('FTS_RUN_ASTERISK_TEST' in os.environ,
    "Asterisk tests disabled")
class TestAsteriskHttpClient(LiveServerTestCase, FTSenderBaseTest):

    def test_raises_permission_denied(self):
        client = AsteriskHttpClient()
        with self.assertRaises(AsteriskHttpResponseWithError):
            client.get_status()

    def test_login_fails(self):
        client = AsteriskHttpClient()

        asterisk_settings = dict(settings.ASTERISK)
        asterisk_settings['USERNAME'] = ''
        asterisk_settings['PASSWORD'] = ''

        with self.settings(ASTERISK=asterisk_settings):
            with self.assertRaises(AsteriskHttpAuthenticationFailedError):
                client.login()

    def test_anon_ping_fails(self):
        client = AsteriskHttpClient()
        with self.assertRaises(AsteriskHttpResponseWithError):
            client.ping()

    def test_login(self):
        client = AsteriskHttpClient()
        client.login()

    def test_ping_y_status(self):
        client = AsteriskHttpClient()
        client.login()
        client.ping()
        client.get_status()

    def test_originate_fails(self):
        client = AsteriskHttpClient()
        client.login()
        client.ping()
        with self.assertRaises(AsteriskHttpOriginateError):
            client.originate("Local/123@this-context-doesnt-exists",
                "non-existing-ctx", "100", "1", 10000, True, {})

    #
    # Algunos comandos para ejecutar, pero que no son tests
    #

    def dump_status(self):
        client = AsteriskHttpClient()
        client.login()
        client.ping()
        parser = client.get_status()
        pprint.pprint(parser.calls_dicts)

    def login_y_originate(self):
        client = AsteriskHttpClient()
        client.login()
        client.ping()
        client.originate("IAX2/172.19.1.101/319751355727335",
            "from_test_server", "100", "1", 10000)

    def login_y_originate_local_channel(self):
        client = AsteriskHttpClient()
        client.login()
        client.ping()
        client.originate("Local/11223344-319751355727335@FTS-dialer-local-C",
            "from_test_server", "100", "1", 10000)

    def login_y_originate_local_channel_async(self):
        client = AsteriskHttpClient()
        client.login()
        client.ping()
        client.originate("Local/11223344-319751355727335@FTS-dialer-local-C",
            "from_test_server", "100", "1", 10000, True, {})

    def login_y_originate_local_channel_dump_vars(self):
        client = AsteriskHttpClient()
        client.login()
        client.ping()
        variables = {
            'TURNO_dia': '12',
            'TURNO_mes': 'agosto',
            'TURNO_anio': '1999',
            'NOMBRE_Y_APELLIDO': 'Juan Perez',
        }
        client.originate("Local/893478947892@from_test_server",
            "from_test_server", "893478947892", "1", 10000, True, variables)

    def ping_sin_login(self):
        client = AsteriskHttpClient()
        client.ping()

    def login_dos_veces(self):
        client = AsteriskHttpClient()
        client.login()
        client.login()
