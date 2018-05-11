# -*- coding: utf-8 -*-

import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

TEST_RUNNER = "fts_daemon.tests.st.test_system_test.FTSenderSystemTestDiscoverRunner"

DEBUG = True
TEMPLATE_DEBUG = DEBUG
FTS_ENHANCED_URLS = True

# SECRET_KEY = 'xxx'

MEDIA_ROOT = os.path.join(BASE_DIR, '/opt/fts-integration-testing/media_root')
if not os.path.exists(MEDIA_ROOT):
    print ""
    print ""
    print ""
    print ""
    print "********** <ERROR> ****************************************"
    print ""
    print " No se encontro el directorio para MEDIA_ROOT: {0}".format(
        MEDIA_ROOT)
    print "   $ sudo mkdir -p {0}".format(MEDIA_ROOT)
    print "   $ sudo chown $UID {0}".format(MEDIA_ROOT)
    print ""
    print "********** </ERROR> ****************************************"
    print ""
    print ""
    print ""
    print ""

STATIC_ROOT = os.path.join(BASE_DIR, 'dev', 'static_root')

FTS_PROGRAMAR_CAMPANA_FUNC = "_programar_campana_postgresql"

ASTERISK = {
    'USERNAME': 'admin',
    'PASSWORD': 'admin',
    'HTTP_AMI_URL': 'http://172.17.42.1:7089',
    'DIAL_URL': "IAX2/127.0.0.1/${NumberToCall}",
}

# Para usar Asterisk@Docker
FTS_DIALPLAN_FILENAME = os.path.join(BASE_DIR,
    "deploy/docker-dev/asterisk/fts-conf-integration-testing/"
    "extensions_fts.conf")

# Para usar Asterisk@Docker
FTS_QUEUE_FILENAME = os.path.join(BASE_DIR,
    "deploy/docker-dev/asterisk/fts-conf-integration-testing/"
    "queues_fts.conf")

# Para usar Asterisk@Docker
FTS_RELOAD_CMD = [os.path.join(BASE_DIR,
    "deploy/docker-dev/reload_asterisk_integration_testing.sh")]

# Ubuntu (wav -> wav)
TMPL_FTS_AUDIO_CONVERSOR = ["sox", "-t", "wav", "<INPUT_FILE>",
    "-r", "8k", "-c", "1", "-e", "signed-integer",
    "-t", "wav", "<OUTPUT_FILE>"]

TMPL_FTS_AUDIO_CONVERSOR_EXTENSION = ".wav"

FTS_AGI_DAEMON_HOST = "172.17.42.1"

#
# *NO SABEMOS* el url, porque el puerto se sabrá al momento
#    de ejecutar el test (LiveServerTestCase utilizara un puerto
#    que encuentre libre al ejecutar el test).
#
#FTS_FAST_AGI_DAEMON_PROXY_URL = "http://localhost:8080"
FTS_FAST_AGI_DAEMON_PROXY_URL = "http://localhost:1"

FTS_DAEMON_ORIGINATES_PER_SECOND = 100.0

FTS_FDCD_LOOP_SLEEP = 5.0

FTS_FDCD_INITIAL_WAIT = 0.5

FTS_BASE_DATO_CONTACTO_DUMP_PATH = "/tmp/"

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': ('%(asctime)-15s [%(levelname)7s] '
                '%(name)20s - %(message)s')
        },
    },
    'filters': {
    },
    'handlers': {
        'null': {
            'level': 'DEBUG',
            'class': 'logging.NullHandler',
        },
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'verbose'
        },
    },
    'loggers': {
        '': {
            'handlers': ['console'],
            'level': 'INFO',
        },
        'south': {
            'handlers': ['console'],
            'level': 'INFO',
        },
        'django.db.backends': {
            'handlers': ['console'],
            'level': 'INFO',
        },
        'requests': {
            'handlers': ['console'],
            'level': 'WARNING',
        },
        'AMI': {
            'handlers': ['console'],
            'level': 'WARNING',
        },
        'FastAGI': {
            'handlers': ['console'],
            'level': 'WARNING',
        }
    }
}

if 'FTS_DEBUG' in os.environ:
    LOGGING['loggers']['']['level'] = 'DEBUG'
