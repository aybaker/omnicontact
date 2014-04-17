# -*- coding: utf-8 -*-

import os
BASE_DIR = os.path.dirname(os.path.dirname(__file__))

DEBUG = True
TEMPLATE_DEBUG = DEBUG

ADMINS = (
    # ('Your Name', 'your_email@example.com'),
)

MANAGERS = ADMINS

FTS_ENHANCED_URLS = True

MEDIA_ROOT = '/home/username/ftsenderweb/media_files/'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': 'ftsenderweb_db',
        'USER': 'ftsenderweb',
        'PASSWORD': 'XXXXXXXXX',
        'HOST': 'localhost',
        'PORT': '',
    }
}

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),
    }
}

SELENIUM_WEBDRIVER_BIN = (
    # Ubuntu 13.04 / Ubuntu 13.10 - Package: 'chromium-chromedriver'
    '/usr/lib/chromium-browser/chromedriver',
)

FTS_DIALPLAN_FILENAME = "/tmp/extensions_fts.conf"

FTS_QUEUE_FILENAME = "/tmp/queues_fts.conf"

FTS_RELOAD_CMD = ["/usr/bin/logger", "reload-asterisk"]

TMPL_FTS_AUDIO_CONVERSOR = ["sox", "<INPUT_FILE>", "<OUTPUT_FILE>"]

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
        }
    }
}

