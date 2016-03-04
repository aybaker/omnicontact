# -*- coding: utf-8 -*-
#@PydevCodeAnalysisIgnore
#
#
# WARNING!!! ATENCION!!! WAARSCHUWING!!! WARNUNG!!! AVIS!!!
# WARNING!!! ATENCION!!! WAARSCHUWING!!! WARNUNG!!! AVIS!!!
# WARNING!!! ATENCION!!! WAARSCHUWING!!! WARNUNG!!! AVIS!!!
#
#
#              uuuuuuuuuuuuuuuuuuuu
#            u" uuuuuuuuuuuuuuuuuu "u
#          u" u$$$$$$$$$$$$$$$$$$$$u "u
#        u" u$$$$$$$$$$$$$$$$$$$$$$$$u "u
#      u" u$$$$$$$$$$$$$$$$$$$$$$$$$$$$u "u
#    u" u$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$u "u
#  u" u$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$u "u
#  $ $$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$ $
#  $ $$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$ $
#  $ $$$" ... "$...  ...$" ... "$$$  ... "$$$ $
#  $ $$$u `"$$$$$$$  $$$  $$$$$  $$  $$$  $$$ $
#  $ $$$$$$u  "$$$$  $$$  $$$$$  $$  """ u$$$ $
#  $ $$$""$$$  $$$$  $$$u "$$$" u$$  $$$$$$$$ $
#  $ $$$$....,$$$$$..$$$$$....,$$$$..$$$$$$$$ $
#  $ $$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$ $
#  "u "$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$" u"
#    "u "$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$" u"
#      "u "$$$$$$$$$$$$$$$$$$$$$$$$$$$$" u"
#        "u "$$$$$$$$$$$$$$$$$$$$$$$$" u"
#          "u "$$$$$$$$$$$$$$$$$$$$" u"
#            "u """""""""""""""""" u"
#              """"""""""""""""""""
#
#
# Este archivo es autogenerado con cada deploy.
# Cualquier modificacion que se realice aqui sera
#  sobreescrita sin mayores advertencias que las presentes
#
# WARNING!!! ATENCION!!! WAARSCHUWING!!! WARNUNG!!! AVIS!!!
# WARNING!!! ATENCION!!! WAARSCHUWING!!! WARNUNG!!! AVIS!!!
# WARNING!!! ATENCION!!! WAARSCHUWING!!! WARNUNG!!! AVIS!!!
#

"""
Template para generar ftsw_web_settings_local para deploys.
"""

import os

DEBUG = False
TEMPLATE_DEBUG = DEBUG

ADMINS = (
    # ('Your Name', 'your_email@example.com'),
)

ALLOWED_HOSTS = [
    "*",
]

SECRET_KEY = '{{dj_sett_SECRET_KEY}}'

MANAGERS = ADMINS

MEDIA_ROOT = '/home/ftsender/deploy/media_root/'

STATIC_ROOT = "/home/ftsender/deploy/static_root/"

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'HOST': '127.0.0.1',
        'NAME': 'ftsender',
        'USER': 'ftsender',
        'PASSWORD': '{{db_password}}',
        'CONN_MAX_AGE': 300,
        'ATOMIC_REQUESTS': True,
    }
}

CACHES = {
    'default': {
        'BACKEND': 'redis_cache.cache.RedisCache',
        'LOCATION': '127.0.0.1:6379:1',
        'OPTIONS': {
            'CLIENT_CLASS': 'redis_cache.client.DefaultClient',
            # 'CONNECTION_POOL_KWARGS': {'max_connections': 100}
            # 'SOCKET_TIMEOUT': 5,  # in seconds
            # 'IGNORE_EXCEPTIONS': True,
        }
    }
}

INTERNAL_IPS = (
    "127.0.0.1",
)

ASTERISK = {
    'USERNAME': '{{dj_sett_ASTERISK_USERNAME}}',
    'PASSWORD': '{{dj_sett_ASTERISK_PASSWORD}}',
    'HTTP_AMI_URL': '{{dj_sett_ASTERISK_HTTP_AMI_URL}}',
    'DIAL_URL': "{{dj_sett_ASTERISK_DIAL_URL}}",
}

# Server donde realizar request desde AGI PROXY => NGINX
FTS_FAST_AGI_DAEMON_PROXY_URL = '{{dj_sett_FTS_FAST_AGI_DAEMON_PROXY_URL}}'

FTS_DIALPLAN_FILENAME = '{{dj_sett_FTS_DIALPLAN_FILENAME}}'

FTS_QUEUE_FILENAME = '{{dj_sett_FTS_QUEUE_FILENAME}}'

FTS_RELOAD_CMD = {{dj_sett_FTS_RELOAD_CMD}}

TMPL_FTS_AUDIO_CONVERSOR = {{dj_sett_TMPL_FTS_AUDIO_CONVERSOR}}

TMPL_FTS_AUDIO_CONVERSOR_EXTENSION = '{{dj_sett_TMPL_FTS_AUDIO_CONVERSOR_EXTENSION}}'

FTS_BASE_DATO_CONTACTO_DUMP_PATH = '{{dj_sett_FTS_BASE_DATO_CONTACTO_DUMP_PATH}}'

FTS_LIMITE_GLOBAL_DE_CANALES = {{dj_sett_FTS_LIMITE_GLOBAL_DE_CANALES}}

FTS_SMS_UTILIZADO = '{{dj_sett_FTS_SMS_UTILIZADO}}'

FTS_LIMITE_GLOBAL_DE_CHIPS = {{dj_sett_FTS_LIMITE_GLOBAL_DE_CHIPS}}

_logging_output_file = os.environ.get("FTS_LOGFILE", "django.log")
assert os.path.split(_logging_output_file)[0] == "",\
    "La variable de entorno FTS_LOGFILE solo debe contener " +\
    "el nombre del archivo, SIN directorios."

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
            'level': 'ERROR',
            'class': 'logging.StreamHandler',
            'formatter': 'verbose'
        },
        'file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': '/home/ftsender/deploy/log/{0}'.format(_logging_output_file),
            'formatter': 'verbose'
        },
    },
    'loggers': {
        '': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
        },
        'AMI': {
            'handlers': ['console', 'file'],
            'level': 'WARNING',
        },
        'FastAGI': {
            'handlers': ['console', 'file'],
            'level': 'WARNING',
        },
        'twisted': {
            'handlers': ['console', 'file'],
            'level': 'WARNING',
        },
    }
}

#
# WARNING!!! ATENCION!!! WAARSCHUWING!!! WARNUNG!!! AVIS!!!
# WARNING!!! ATENCION!!! WAARSCHUWING!!! WARNUNG!!! AVIS!!!
# WARNING!!! ATENCION!!! WAARSCHUWING!!! WARNUNG!!! AVIS!!!
#
#
#              uuuuuuuuuuuuuuuuuuuu
#            u" uuuuuuuuuuuuuuuuuu "u
#          u" u$$$$$$$$$$$$$$$$$$$$u "u
#        u" u$$$$$$$$$$$$$$$$$$$$$$$$u "u
#      u" u$$$$$$$$$$$$$$$$$$$$$$$$$$$$u "u
#    u" u$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$u "u
#  u" u$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$u "u
#  $ $$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$ $
#  $ $$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$ $
#  $ $$$" ... "$...  ...$" ... "$$$  ... "$$$ $
#  $ $$$u `"$$$$$$$  $$$  $$$$$  $$  $$$  $$$ $
#  $ $$$$$$u  "$$$$  $$$  $$$$$  $$  """ u$$$ $
#  $ $$$""$$$  $$$$  $$$u "$$$" u$$  $$$$$$$$ $
#  $ $$$$....,$$$$$..$$$$$....,$$$$..$$$$$$$$ $
#  $ $$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$ $
#  "u "$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$" u"
#    "u "$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$" u"
#      "u "$$$$$$$$$$$$$$$$$$$$$$$$$$$$" u"
#        "u "$$$$$$$$$$$$$$$$$$$$$$$$" u"
#          "u "$$$$$$$$$$$$$$$$$$$$" u"
#            "u """""""""""""""""" u"
#              """"""""""""""""""""
#
#
# Este archivo es autogenerado con cada deploy.
# Cualquier modificacion que se realice aqui sera
#  sobreescrita sin mayores advertencias que las presentes
#
# WARNING!!! ATENCION!!! WAARSCHUWING!!! WARNUNG!!! AVIS!!!
# WARNING!!! ATENCION!!! WAARSCHUWING!!! WARNUNG!!! AVIS!!!
# WARNING!!! ATENCION!!! WAARSCHUWING!!! WARNUNG!!! AVIS!!!
#
