# -*- coding: utf-8 -*-

"""Metodos utilitarios para ser reutilizados en los distintos
system tests.
"""

from __future__ import unicode_literals

import logging
import os

from unittest.case import skipUnless
from django.conf import settings
from django.test.runner import DiscoverRunner
from django.test.testcases import LiveServerTestCase
from django.test.utils import override_settings
import subprocess
import time
from fts_daemon.asterisk_ami_http import AsteriskHttpClient


class FTSenderSystemTestDiscoverRunner(DiscoverRunner):

    def __init__(self, *args, **kwargs):
        settings.FTS_TESTING_MODE = True

        for db in settings.DATABASES.values():
            if db.get('CONN_MAX_AGE', 0) != 0:
                print "Patcheando CONN_MAX_AGE: {0} -> 0".format(
                    db['CONN_MAX_AGE'])
                db['CONN_MAX_AGE'] = 0

        for key in os.environ.keys():
            if key.find("proxy") > -1:
                del os.environ[key]

        # ----- Settings para Celery -----
        # POR AHORA hacemos que los tasks Celery sean
        # ejecutados localmente, hasta q' implementemos
        # la infraestructura necesaria para lanzar workers
        # Celery.
        settings.CELERY_ALWAYS_EAGER = True
        settings.CELERY_EAGER_PROPAGATES_EXCEPTIONS = True

        super(FTSenderSystemTestDiscoverRunner,
              self).__init__(*args, **kwargs)

        def handleError(self, record):
            raise

        logging.Handler.handleError = handleError


@skipUnless("FTS_SYSTEM_TEST" in os.environ, "Solo para System Tests")
class FTSenderSystemBaseTest(LiveServerTestCase):

    @classmethod
    def set_base_dir(cls):
        tmpdir = os.path.dirname(__file__)
        tmpdir = os.path.abspath(tmpdir)
        # tmpdir -> PROYECTO/fts_daemon/tests/st
        tmpdir = os.path.split(tmpdir)[0]
        # tmpdir -> PROYECTO/fts_daemon/tests
        tmpdir = os.path.split(tmpdir)[0]
        # tmpdir -> PROYECTO/fts_daemon
        tmpdir = os.path.split(tmpdir)[0]
        # tmpdir -> PROYECTO
        cls.base_dir = tmpdir

    @classmethod
    def launch_process(cls, target):
        process = subprocess.Popen(target + " -d", shell=True)
        return process

    @classmethod
    def wait_for_asterisk(cls):
        while True:
            print "Intentando contactar Asterisk..."
            client = AsteriskHttpClient()
            try:
                client.login()
                print "AsteriskHttpClient: LOGIN OK :-D"
                return
            except:
                print " (no se pudo contactar a Asterisk)"
            time.sleep(500)

    @classmethod
    def launch_asterisk(cls):
        # script = os.path.join(cls.base_dir,
        #     "deploy/docker-dev/run_integration_testing.sh")
        # assert os.path.exists(script), (""
        #     "No se encontro el script de inicio de Asterisk "
        #     "en " + script)
        # cls.asterisk_process = cls.launch_process(script)
        cls.wait_for_asterisk()

    @classmethod
    def stop_asterisk(cls):
        # cls.asterisk_process.terminate()
        # print "Haciendo asterisk_process.join()..."
        # count = 5
        # while cls.asterisk_process.poll() is None and count > 0:
        #     print "asterisk_process todavia corriendo... Esperando..."
        #     time.sleep(1000)
        #     count = count - 1
        # if cls.asterisk_process.poll() is not None:
        #     cls.asterisk_process.kill()
        pass

    @classmethod
    def launch_fastagi_daemon(cls):
        script = os.path.join(cls.base_dir,
            "fts_daemon/fastagi_daemon.py")
        assert os.path.exists(script), (""
            "No se encontro el script de inicio de fast agi daemon "
            "en " + script)
        cls.fastagi_daemon_process = cls.launch_process(script)

    @classmethod
    def stop_fastagi_daemon(cls):
        pass

    @classmethod
    def launch_poll_daemon(cls):
        script = os.path.join(cls.base_dir,
            "fts_daemon/poll_daemon/main.py")
        assert os.path.exists(script), (""
            "No se encontro el script de inicio de poll daemon "
            "en " + script)
        cls.poll_daemon_process = cls.launch_process(script)

    @classmethod
    def stop_poll_daemon(cls):
        pass

    @classmethod
    def setUpClass(cls):
        super(FTSenderSystemBaseTest, cls).setUpClass()
        print "FTSenderSystemBaseTest.setUpClass()"
        cls.set_base_dir()
        cls.launch_asterisk()
        cls.launch_fastagi_daemon()
        cls.launch_poll_daemon()

    @classmethod
    def tearDownClass(cls):
        super(FTSenderSystemBaseTest, cls).tearDownClass()
        print "FTSenderSystemBaseTest.tearDownClass()"
        cls.stop_asterisk()

    def test_uno(self):
        url = self.live_server_url
        with override_settings(FTS_FAST_AGI_DAEMON_PROXY_URL=url):
            pass

    def test_dos(self):
        url = self.live_server_url
        with override_settings(FTS_FAST_AGI_DAEMON_PROXY_URL=url):
            pass
