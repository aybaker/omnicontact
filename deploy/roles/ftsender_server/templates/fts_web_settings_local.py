# -*- coding: utf-8 -*-

DEBUG = False
TEMPLATE_DEBUG = DEBUG

ADMINS = (
    # ('Your Name', 'your_email@example.com'),
)

ALLOWED_HOSTS = [
    "*",
]

SECRET_KEY = 'aewemwobFat7ShobEsUj5BibIpAfus5'

MANAGERS = ADMINS

MEDIA_ROOT = '/home/ftsender/deploy/media_root'

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

SELENIUM_WEBDRIVER_BIN = (
    # Ubuntu 13.04 / Ubuntu 13.10 - Package: 'chromium-chromedriver'
    '/usr/lib/chromium-browser/chromedriver',
)

INTERNAL_IPS = (
    "127.0.0.1",
)

ASTERISK = {
    'USERNAME': 'astermind',
    'PASSWORD': 'astermindXdd',
    'HTTP_AMI_URL': 'http://192.168.122.27:7088',
    'DIAL_URL': "IAX2/192.168.122.24/${NumberToCall}",
}

# Server donde realizar request desde AGI PROXY => NGINX
FTS_FAST_AGI_DAEMON_PROXY_URL = "http://vm.centos-6-fts:8088"

FTS_DIALPLAN_FILENAME = "/opt/data-tsunami/asterisk-11-d/etc/" +\
    "asterisk/fts/extensions.conf"

FTS_QUEUE_FILENAME = "/opt/data-tsunami/asterisk-11-d/etc/" +\
    "asterisk/fts/queues_fts.conf"

FTS_RELOAD_CMD = ["sudo", "-u", "asterisk",
    "/opt/data-tsunami/asterisk-11-d/sbin/asterisk",
    "-x", "dialplan reload"]

# CentOS
#TMPL_FTS_AUDIO_CONVERSOR = ["sox",
#    "-t", "wav", "<INPUT_FILE>",
#    "-t", "gsm", "-r", "8000", "-c", "1", "-b", "<OUTPUT_FILE>"
#]

#TMPL_FTS_AUDIO_CONVERSOR = ["sox",
#    "-t", "wav", "<INPUT_FILE>",
#    "-t", "gsm", "-r", "8000", "-c", "1", "<OUTPUT_FILE>"
#]
#
#TMPL_FTS_AUDIO_CONVERSOR_EXTENSION = ".gsm"

# Probamos con wav-wav
TMPL_FTS_AUDIO_CONVERSOR = ["sox", "-t", "wav", "<INPUT_FILE>",
    "-r", "8k", "-c", "1", "-e", "signed-integer",
    "-t", "wav", "<OUTPUT_FILE>"]

TMPL_FTS_AUDIO_CONVERSOR_EXTENSION = ".wav"

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
            'filename': '/home/ftsender/deploy/log/django.log',
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
