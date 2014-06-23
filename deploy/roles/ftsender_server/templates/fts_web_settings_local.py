# -*- coding: utf-8 -*-
#@PydevCodeAnalysisIgnore

"""
Template para generar ftsw_web_settings_local para deploys.
"""


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
        'BACKEND': 'uwsgicache.UWSGICache',
    }
}

SELENIUM_WEBDRIVER_BIN = (
    # Ubuntu 13.04 / Ubuntu 13.10 - Package: 'chromium-chromedriver'
    '/usr/lib/chromium-browser/chromedriver',
)

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
            'filename': '{{dj_sett_DJANGO_LOG_FILE}}',
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
