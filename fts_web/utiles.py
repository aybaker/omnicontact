# -*- coding: utf-8 -*-

'''
Created on Apr 15, 2014

@author: Horacio G. de Oro
'''

from __future__ import unicode_literals
import re
import time
import uuid


SUBSITUTE_REGEX = re.compile(r'[^a-z\._-]')


def _upload_to(prefix, max_length, instance, filename):
    filename = SUBSITUTE_REGEX.sub('', filename)
    return "{0}/%Y/%m/{1}-{2}".format(prefix,
        str(uuid.uuid4()), filename)[:max_length]


def upload_to(prefix, max_length):
    def func(instance, filename):
        return _upload_to(prefix, max_length, instance, filename)
    return func


def resolve_strftime(text):
    return time.strftime(text) # time.gmtime()
