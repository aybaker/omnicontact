# -*- coding: utf-8 -*-
from __future__ import unicode_literals

'''
Created on Mar 27, 2014

@author: Horacio G. de Oro
'''

from starpy import manager


def ami_login(username, password, server, port):
    """Logins to Asterisk AMI.
    Returns: AMI protocol instance
    """
    factory = manager.AMIFactory(username, password)
    ami_protocol = factory.login(server, port)
    return ami_protocol


def originate(ami, outgoing_channel, context, exten, priority, timeout):
    # TODO: docs. dicen q' `timeout` no es estandar en Asterisk.
    # ¿a q' se refieren?
    ami.originate(outgoing_channel, context, exten, priority, timeout)
