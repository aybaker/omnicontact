# -*- coding: utf-8 -*-

"""Mocks"""

from __future__ import unicode_literals

from fts_daemon.asterisk_ami_http import AsteriskHttpResponseWithError,\
    AsteriskHttpOriginateError, AsteriskHttpAuthenticationFailedError

_pkg = "fts_tests.tests.tests_asterisk_ami_http_mocks."


class AsteriskAmiHttpClientBaseMock(object):
    """Mock"""

    NAME = _pkg + "AsteriskAmiHttpClientBaseMock"

    def __init__(self):
        self.logged_in = False

    def login(self):
        # loguearnos mas de 1 vez está ok
        self.logged_in = True

    def ping(self):
        if not self.logged_in:
            raise AsteriskHttpResponseWithError("no esta logueado")

    def originate(self, *args, **kwargs):
        if not self.logged_in:
            raise AsteriskHttpResponseWithError("no esta logueado")


class AAHCOriginateErrorMock(AsteriskAmiHttpClientBaseMock):
    """Mock: ORIGINATE falla. Simula problema con context, etc."""

    NAME = _pkg + "AAHCOriginateErrorMock"

    def originate(self, *args, **kwargs):
        super(AAHCOriginateErrorMock, self).originate(*args, **kwargs)
        raise AsteriskHttpOriginateError()


class AAHCAuthFailMock(AsteriskAmiHttpClientBaseMock):
    """Mock: autenticacion falla. Simula usuario/password incorrecto"""

    NAME = _pkg + "AAHCAuthFailMock"

    def login(self):
        raise AsteriskHttpAuthenticationFailedError()
