# -*- coding: utf-8 -*-

"""
Defaults para ambientes de desarrollo.

Para utilizar estos settings, crear ``fts_web_settings_local``
(en paquete ROOT de Python) con:

    from fts_web_settings_local_dev import *  # @UnusedWildImport
    SECRET_KEY = 'xxx' # Algun valor random

Y luego de eso, las customizaciones.

"""

import os

from fts_tests.models import customize_INSTALLED_APPS

BASE_DIR = os.path.dirname(__file__)

DEBUG = True
TEMPLATE_DEBUG = DEBUG
FTS_ENHANCED_URLS = True

# SECRET_KEY = 'xxx'

MEDIA_ROOT = os.path.join(BASE_DIR, 'media_root')

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),
    }
}

if 'USE_PG' in os.environ:
    FTS_PROGRAMAR_CAMPANA_FUNC = "_programar_campana_postgresql"

INTERNAL_IPS = (
    "127.0.0.1",
)

ASTERISK = {
    'USERNAME': 'asterisk',
    'PASSWORD': 'asterisk',
    'HTTP_AMI_URL': 'http://127.0.0.1:1',
}

FTS_DIALPLAN_FILENAME = "/tmp/fts-extensions.conf"

FTS_QUEUE_FILENAME = "/tmp/fts-queues.conf"

FTS_RELOAD_CMD = ["/bin/true"]

# Ubuntu (wav -> wav)
TMPL_FTS_AUDIO_CONVERSOR = ["sox", "-t", "wav", "<INPUT_FILE>",
    "-r", "8k", "-c", "1", "-e", "signed-integer",
    "-t", "wav", "<OUTPUT_FILE>"]

TMPL_FTS_AUDIO_CONVERSOR_EXTENSION = ".wav"

FTS_FAST_AGI_DAEMON_PROXY_URL = "http://localhost:8080"

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
            'class': 'django.utils.log.NullHandler',
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

if 'FTS_DISABLE_LOGGING' in os.environ:
    LOGGING['handlers']['console']['class'] = 'django.utils.log.NullHandler'

FTS_DUMP_HTTP_AMI_RESPONSES = 'FTS_DUMP_HTTP_AMI_RESPONSES' in os.environ

FTS_SETTING_CUSTOMIZERS = [customize_INSTALLED_APPS]

if 'FTS_SIMULADOR_DAEMON' in os.environ:
    # Apunta a uWSGI
    ASTERISK['HTTP_AMI_URL'] = 'http://127.0.0.1:8080/asterisk-ami-http/simulador'  #@IgnorePep8
    FTS_TESTING_MODE = True
    FTS_DAEMON_SLEEP_SIN_TRABAJO = 0.1
    FTS_DAEMON_SLEEP_LIMITE_DE_CANALES = 0.1
