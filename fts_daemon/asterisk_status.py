# -*- coding: utf-8 -*-

"""Parser de XML que devuelve Asterisk"""

from __future__ import unicode_literals

import httplib

from django.conf import settings
from fts_web.errors import FtsError
import logging as _logging
import xml.etree.ElementTree as ET


logger = _logging.getLogger(__name__)


class AsteriskXmlParser(object):
    """Base class for parsing various responses from Asterisk"""

    def parse(self, xml):
        raise NotImplementedError()

    def _parse_and_check(self, xml):
        """Parses the XML string and do basic checks.
        Returns the 'root' element
        """

        # https://docs.python.org/2.6/library/xml.etree.elementtree.html
        logger.debug("Iniciando parseo... XML:\n%s", xml)
        root = ET.fromstring(xml)
        logger.debug("Parseo finalizado")

        self._check(root)

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

    def _check(self, root):
        """This method checks the response for known problems or errors
        Parameters:
            - root: the root of the doc docuement
        Raises:
            - AsteriskHttpPermissionDeniedError
        """

        # <ajax-response>
        # <response type='object' id='unknown'>
        #    <generic response='Error' message='Permission denied' />
        # </response>
        # </ajax-response>

        elements = root.findall("./response/generic")
        if len(elements) != 1:
            return

        response = elements[0].attrib.get('response', '').lower()
        message = elements[0].attrib.get('message', '').lower()

        if response == 'error' and message == 'permission denied':
            raise AsteriskHttpPermissionDeniedError()


class AsteriskLoginXmlParserElementTree(AsteriskXmlParser):
    """Parses the XML returned by Asterisk when
    requesting `/mxml?action=login`
    """

    def parse(self, xml):
        """Parsea XML y guarda resultado en `self.calls_dicts`
        """
        # <ajax-response>
        #     <response type='object' id='unknown'>
        #        <generic response='Success'
        #            message='Authentication accepted' />
        #    </response>
        # </ajax-response>

        # <generic response="Error" message="Authentication failed"/>

        root = self._parse_and_check(xml)
        response_dict = self.get_response_on_first_element(root)
        response = response_dict.get('response', '').lower()

        if response != 'success':
            raise AsteriskHttpAuthenticationFailedError()


AsteriskLoginXmlParser = AsteriskLoginXmlParserElementTree


class AsteriskStatusXmlParserElementTree(AsteriskXmlParser):
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


AsteriskStatusXmlParser = AsteriskStatusXmlParserElementTree


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
        parser = AsteriskLoginXmlParser()
        parser.parse(response_body)
        return parser

    def get_status(self):
        url = "/mxml?action=status"
        response_body, _ = self._request(url)

        parser = AsteriskStatusXmlParser()
        parser.parse(response_body)
        return parser


#==============================================================================
# Errors
#==============================================================================

class AsteriskHttpStatus(FtsError):
    """Base class for exceptions related to the retrieval of information
    from Asterisk using http + xml
    """


class AsteriskHttpPermissionDeniedError(AsteriskHttpStatus):
    """The Asterisk Http interface returned 'permission denied'"""
    pass


class AsteriskHttpAuthenticationFailedError(AsteriskHttpStatus):
    """The authentication failed"""
    pass
