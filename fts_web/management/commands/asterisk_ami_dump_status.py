# -*- coding: utf-8 -*-
"""
Muestra status de Asterisk, reportado por AsteriskHttpClient()
"""

from __future__ import unicode_literals

from optparse import make_option
import os
import pprint
import re
import time

from django.core.management.base import BaseCommand
from fts_daemon.asterisk_ami_http import AsteriskHttpClient


# Local/51-620@FTS_local_campana_16-00000045
REGEX = re.compile("^Local/([0-9]+)-([0-9]+)@FTS_local_campana_([0-9]+)")


class Command(BaseCommand):
    option_list = BaseCommand.option_list + (
        make_option('--full', action='store_true', dest='full', default=False),
        make_option('--lines', action='store_true', dest='lines',
            default=False),
    )

    def _print(self, calls_dicts):
        # Local/28-620@FTS_local_campana
        datos = set()
        for item in calls_dicts:
            if "channel" in item:
                match_obj = REGEX.match(item["channel"])
                if match_obj:
                    contacto_id = match_obj.group(1)
                    numero = match_obj.group(2)
                    campana_id = match_obj.group(3)
                    datos.add("{0}-{1}-{2}".format(
                        contacto_id, numero, campana_id))
        for dato in sorted(datos):
            print(dato)
        if datos:
            print " - {0} cx".format(len(datos))

    def handle(self, *args, **options):
        for key in os.environ.keys():
            if key.find("proxy") > -1:
                del os.environ[key]

        client = AsteriskHttpClient()
        client.login()
        client.ping()
        calls_dicts = None
        while True:
            # subprocess.call("clear")
            if calls_dicts or calls_dicts is None:
                print "# ---------- "

            calls_dicts = client.get_status().calls_dicts

            if options['full']:
                if calls_dicts:
                    pprint.pprint(calls_dicts)
            else:
                if options['lines']:
                    for item in calls_dicts:
                        print ",".join([k + ":" + item[k]
                            for k in sorted(item.keys())])
                else:
                    self._print(calls_dicts)
            time.sleep(1)
