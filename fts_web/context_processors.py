#-*- coding: utf-8 -*-

"""
Context processors customizados para la aplicación
"""

from __future__ import unicode_literals

from django.conf import settings


def testing_mode(request):
    """Setea variable `testing_mode` si se están ejecutando
    los test cases.
    """
    return {'testing_mode': settings.FTS_TESTING_MODE}

def reporte_sms(request):
    """Setea variable .
    """
    return {'reporte_sms_url': settings.FTS_REPORTE_SMS_URL}
