#-*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.conf import settings


def testing_mode(request):
    return {'testing_mode': settings.TESTING_MODE}
