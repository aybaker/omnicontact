# -*- coding: utf-8 -*-

"""Parser de XML que devuelve Asterisk"""

from __future__ import unicode_literals

import httplib

from django.conf import settings
from fts_web.errors import FtsError
import logging as _logging
import xml.etree.ElementTree as ET


logger = _logging.getLogger(__name__)


#==============================================================================
# Parser of XML responses
#==============================================================================

class AsteriskXmlParser(object):
    """Base class for parsing various responses from Asterisk"""

    def __init__(self):
        self.response_dict = None

    def parse(self, xml):
        raise NotImplementedError()

    def _parse_and_check(self, xml, check_errors=True,
        exception_for_error=None):
        """Parses the XML string, sets self.response_dict and do basic checks.

        Parameters:
            - xml: the XML string
            - check_errors: if True (default) check if the response
                has been set as 'Error'.

        Returns:
            - the 'root' element of the DOM tree
        """

        # https://docs.python.org/2.6/library/xml.etree.elementtree.html
        logger.debug("Iniciando parseo... XML:\n%s", xml)
        root = ET.fromstring(xml)
        logger.debug("Parseo finalizado")

        self.response_dict = self.get_response_on_first_element(root)

        if self.response_dict:
            response_lower = self.response_dict.get('response', '').lower()

            if response_lower == 'error':
                logger.info("_parse_and_check(): found 'response' == 'Error'. "
                    " response_dict: '%s' - XML:\n%s", str(self.response_dict),
                    xml)
                if check_errors:
                    if exception_for_error:
                        raise exception_for_error()
                    else:
                        raise AsteriskHttpResponseWithError()
            elif response_lower == 'success':
                pass
            else:
                logger.warn("_parse_and_check(): unknown 'response'. "
                    "response_dict: '%s' - XML:\n%s", str(self.response_dict),
                    xml)

        return root

    def get_response_on_first_element(self, root):
        """Returns attributes of tag 'generic' if an 'response' attribute
        exists in the first child of root.

        For example, for the folowing response
        # <ajax-response>
        # <response type='object' id='unknown'>
        #    <generic response='Error' message='Permission denied' />
        # </response>
        # </ajax-response>

        this method should return a dict with:

        { response:'Error', message='Permission denied'}

        Returns: a dict (if 'response' found) or `None`
        """
        elements = root.findall("./response/generic")
        if not elements:
            return None

        if 'response' in elements[0].attrib:
            return dict(elements[0].attrib)
        else:
            return None

#    def _check(self, root):
#        """This method checks the response for known problems or errors
#        Parameters:
#            - root: the root of the doc docuement
#        Raises:
#            - AsteriskHttpPermissionDeniedError
#        """
#
#        # <ajax-response>
#        # <response type='object' id='unknown'>
#        #    <generic response='Error' message='Permission denied' />
#        # </response>
#        # </ajax-response>
#
#        elements = root.findall("./response/generic")
#        if len(elements) != 1:
#            return
#
#        # TODO: evaluar de usar self.get_response_on_first_element()
#
#        response = elements[0].attrib.get('response', '').lower()
#        message = elements[0].attrib.get('message', '').lower()
#
#        # TODO: quiza, si existe 'response' == 'error', ya deberiamos
#        #  lanzar excepcion!
#        if response == 'error' and message == 'permission denied':
#            raise AsteriskHttpPermissionDeniedError()


class AsteriskXmlParserForPing(AsteriskXmlParser):
    """Parses the XML returned by Asterisk when
    requesting `/mxml?action=ping`
    """

    def parse(self, xml):
        """Parses XML and returns `response_dict`
        Raises:
            - AsteriskHttpPingError: if ping failed
        """
        # <generic response='Success' ping='Pong'
        #    timestamp='1398544611.316607'/>

        root = self._parse_and_check(xml)
        response_dict = self.get_response_on_first_element(root)
        response = response_dict.get('response', '').lower()

        if response != 'success':
            raise AsteriskHttpPingError()

        return response_dict


class AsteriskXmlParserForLogin(AsteriskXmlParser):
    """Parses the XML returned by Asterisk when
    requesting `/mxml?action=login`
    """

    def parse(self, xml):
        """Parsea XML.
        Lanza `AsteriskHttpAuthenticationFailedError` si el login fallo.
        """
        # <ajax-response>
        #     <response type='object' id='unknown'>
        #        <generic response='Success'
        #            message='Authentication accepted' />
        #    </response>
        # </ajax-response>

        # <generic response="Error" message="Authentication failed"/>

        self._parse_and_check(xml,
            exception_for_error=AsteriskHttpAuthenticationFailedError)


class AsteriskXmlParserForStatus(AsteriskXmlParser):
    """Parses the XML returned by Asterisk when
    requesting `/mxml?action=status`
    """

    def __init__(self):
        self.calls_dicts = []

    def _element_is_respones_status(self, elem):
        # <generic>.attrib -> {
        #    'message': 'Channel status will follow',
        #    'response': 'Success'
        # }
        if elem.attrib.get('response', '') == 'Success' and \
            'message' in elem.attrib:
            return True
        return False

    def _element_is_event_status_complete(self, elem):
        # <generic event='StatusComplete' items='2' />
        if elem.attrib.get('event', '') == 'StatusComplete':
            return True
        return False

    def _element_is_call_status(self, elem):
        # <generic>.attrib -> {
        #    'event': 'Status',
        #    'privilege': 'Call',
        #
        #    'bridgedchannel': 'SIP/test_user1-00000002',
        #    'connectedlinenum': '<unknown>',
        #    'bridgeduniqueid': '1398522103.5',
        #    'uniqueid': '1398522103.4',
        #    'extension': '319751355727335',
        #    'accountcode': '',
        #    'channelstate': '6',
        #    'calleridnum': '<unknown>',
        #    'priority': '2',
        #    'seconds': '10',
        #    'connectedlinename': '<unknown>',
        #    'context': 'from_test_server',
        #    'calleridname': '<unknown>',
        #    'channel': 'IAX2/asterisk-d-1179',
        #    'channelstatedesc': 'Up'
        # }
        # <generic>.attrib -> {
        #    'event': 'Status',
        #    'privilege': 'Call',
        #
        #    'account': '',
        #    'bridgedchannel': 'IAX2/asterisk-d-1179',
        #    'bridgeduniqueid': '1398522103.4',
        #    'calleridname': '<unknown>',
        #    'calleridnum': '319751355727335',
        #    'channel': 'SIP/test_user1-00000002',
        #    'connectedlinename': '<unknown>',
        #    'connectedlinenum': '<unknown>',
        #    'state': 'Up',
        #    'uniqueid': '1398522103.5'
        # }

        if elem.attrib.get('event', '') == 'Status' and \
            elem.attrib.get('privilege', '') == 'Call':
            return True
        return False

    def _filter_generic_tags(self, elements):
        # response='Success' message='Channel status will follow'
        elem_respones_status = []

        # event='StatusComplete' items='0'
        elem_status_complete = []

        # event='Status' privilege='Call' channel='SIP/test_user1-00000002' ...
        elem_calls = []

        # otros elementos
        elem_unknown = []

        for elem in elements:
            if self._element_is_call_status(elem):
                elem_calls.append(elem)
            elif self._element_is_respones_status(elem):
                elem_respones_status.append(elem)
            elif self._element_is_event_status_complete(elem):
                elem_status_complete.append(elem)
            else:
                elem_unknown.append(elem)

        # TODO: chequear q' haya la cantidad correcta de elementos
        #  en las distintas listas

        assert len(elem_unknown) == 0
        assert len(elem_respones_status) == 1
        assert len(elem_status_complete) == 1

        status_complete_items = int(elem_status_complete[0].attrib.get(
            'items', '-1'))

        assert status_complete_items == len(elem_calls)

        for elem in elem_calls:
            a_dict = dict(elem.attrib)
            self.calls_dicts.append(a_dict)

    def parse(self, xml):
        """Parsea XML y guarda resultado en `self.calls_dicts`
        """
        root = self._parse_and_check(xml)

        # ~~ Lo siguiente NO esta soportado en Python 2.6, asi q' no lo usamos
        # calls = root.findall("./response/generic[@privilege='Call']")

        generic_elements = root.findall("./response/generic")
        try:
            return self._filter_generic_tags(generic_elements)
        except AssertionError:
            logger.warn("XML: %s", xml)
            raise


#==============================================================================
# Asterisk Http Ami Client
#==============================================================================

class AsteriskHttpClient(object):
    """Class to interact with Asterisk using it's http interface"""

    def __init__(self):
        pass

    def _request(self, url):
        """Make requests to the Asterisk.
        Returns tuple with:
            - response_body (contents returned by the server)
            - response object
        """
        # https://docs.python.org/2.6/library/httplib.html
        # FIXME: configure port using settings
        logger.debug("AsteriskHttpClient - _request(): %s", url)
        conn = httplib.HTTPConnection("{0}:7088".format(
            settings.ASTERISK['HOST']))
        conn.request("GET", url)
        response = conn.getresponse()
        logger.debug("AsteriskHttpClient - Response %s %s",
            response.status, response.reason)
        response_body = response.read()
        logger.debug("AsteriskHttpClient - Got http response:\n%s",
            response_body)
        conn.close()

        return response_body, response

    def login(self):
        url = "/mxml?action=login&username={0}&secret={1}".format(
            settings.ASTERISK['USERNAME'],
            settings.ASTERISK['PASSWORD'])
        response_body, _ = self._request(url)
        parser = AsteriskXmlParserForLogin()
        parser.parse(response_body)
        return parser

    def get_status(self):
        url = "/mxml?action=status"
        response_body, _ = self._request(url)

        parser = AsteriskXmlParserForStatus()
        parser.parse(response_body)
        return parser

    def ping(self):
        url = "/mxml?action=ping"
        response_body, _ = self._request(url)

        parser = AsteriskXmlParserForPing()
        parser.parse(response_body)
        return parser


#==============================================================================
# Errors
#==============================================================================

class AsteriskHttpStatus(FtsError):
    """Base class for exceptions related to the retrieval of information
    from Asterisk using http + xml
    """


class AsteriskHttpResponseWithError(AsteriskHttpStatus):
    """The 'response' element (the first child, if has a 'response' attribute)
    was 'Error'.
    """


#class AsteriskHttpPermissionDeniedError(AsteriskHttpStatus):
#    """The Asterisk Http interface returned 'permission denied'"""


class AsteriskHttpAuthenticationFailedError(AsteriskHttpStatus):
    """The authentication failed"""


class AsteriskHttpPingError(AsteriskHttpStatus):
    """The ping failed"""
