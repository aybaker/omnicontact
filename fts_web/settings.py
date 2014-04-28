# -*- coding: utf-8 -*-
"""
Django settings for fts_web project.

For more information on this file, see
https://docs.djangoproject.com/en/1.6/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/1.6/ref/settings/
"""

from __future__ import unicode_literals

import os

from django.contrib import messages


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/1.6/howto/deployment/checklist/
DEBUG = False
TEMPLATE_DEBUG = False

"""Si FTS_ENHANCED_URLS value true, se sirve /media, /static, etc.
En produccion deberia ser FALSE
"""
FTS_ENHANCED_URLS = False

"""Usado en tests de Selenium, en conjunto al metodo `assertTrueSelenium()`.
Si es verdadero y el assert falla, la ejecucion del test es pausada, para
poder ver el mensaje en el navegador.

Ver `assertTrueSelenium()` para mas informacion
"""
FTS_STOP_ON_SELENIUM_ASSERT_ERROR = False

"""Cuantos segundos esperar (mas alla del timeout para ORIGINATE)
para que el proceso hijo termine
"""
FTS_JOIN_TIMEOUT_MARGIN = 5

"""Esta variable vale `True` cuando se estan ejecutando los test."""
FTS_TESTING_MODE = False

"""Path completo (absoluto) al archivo donde se debe generar el dialplan
Ej:
    FTS_DIALPLAN_FILENAME = "/opt/asterisk-11/etc/extensions-ftsender.conf"
    FTS_DIALPLAN_FILENAME = "/opt/asterisk-11/etc/ftsender/extensions.conf"
"""
FTS_DIALPLAN_FILENAME = None

"""Path completo (absoluto) al archivo donde se debe generar queues
Ej:
    FTS_QUEUE_FILENAME = "/opt/asterisk-11/etc/queues-ftsender.conf"
    FTS_QUEUE_FILENAME = "/opt/asterisk-11/etc/ftsender/queues.conf"
"""
FTS_QUEUE_FILENAME = None

"""Comando a ejecutar para hacer reload de Asterisk
Ej:
    FTS_RELOAD_CMD = ["/usr/bin/asterisk", "-x", "reload"]
"""
FTS_RELOAD_CMD = None

"""Comando para convertir audios (wav a gsm)
Ej:
    TMPL_FTS_AUDIO_CONVERSOR = ["sox", "<INPUT_FILE>", "<OUTPUT_FILE>"]

Para transformar WAV (cualquiera) -> WAV (compatible con Asterisk)
    TMPL_FTS_AUDIO_CONVERSOR = ["sox", "-t", "wav", "<INPUT_FILE>",
        "-r", "8k", "-c", "1", "-e", "signed-integer",
        "-t", "wav", "<OUTPUT_FILE>"]
"""
TMPL_FTS_AUDIO_CONVERSOR = None


"""Extension a usar para archivo generado por `TMPL_FTS_AUDIO_CONVERSOR`
Ej: wav
    - por lo tanto, el archivo `<OUTPUT_FILE>` tendra la extension `.wav`
"""
TMPL_FTS_AUDIO_CONVERSOR_EXTENSION = None

"""Booleano que indica si hay que ejecutar tests que implican
una interaccion con Asterisk"""
# TODO: renombrar a FTS_ASTERISK_TEST
ASTERISK_TEST = False

#FTS_ORIGINATE_SERVICE_CLASS = "fts_daemon.asterisk_originate."\
#    "OriginateServiceProcess"

FTS_ASTERISK_HTTP_CLIENT = "fts_daemon.asterisk_ami_http.AsteriskHttpClient"

"""Configuracion para interactuar con Asterisk"""
ASTERISK = {}

# ~~~ Ejemplo ~~~
# ASTERISK = {
#    'USERNAME': 'asteriskadmin',
#    'PASSWORD': 'unpassword',
#    'HOST': '172.19.1.104',
#    'PORT': 5038,
#    'CHANNEL_PREFIX': "IAX2/172.19.1.101/{numberToCall}",
#    'LOCAL_CHANNEL':
#        'Local/{callId}-{numberToCall}@FTS_local_campana_{campanaId}',
#    'CONTEXT': "campania_{campanaId}",
#    'EXTEN': "fts{callId}",
#    'PRIORITY': 1,
#    'TIMEOUT': 5,
#    'HTTP_AMI_URL': 'http://172.19.1.104:7088',
# }


ALLOWED_HOSTS = []

INSTALLED_APPS = (
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'fts_web',
    'south',
    'crispy_forms',
)

MIDDLEWARE_CLASSES = (
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
)

ROOT_URLCONF = 'fts_web.urls'

WSGI_APPLICATION = 'fts_web.wsgi.application'

LANGUAGE_CODE = 'es-ar'

TIME_ZONE = 'America/Argentina/Cordoba'

USE_I18N = True

USE_L10N = True

USE_TZ = True

# https://docs.djangoproject.com/en/1.6/howto/static-files/
STATIC_URL = '/static/'

MEDIA_URL = '/media/'

# Bootstrap friendly
MESSAGE_TAGS = {
    messages.DEBUG: 'alert-info',
    messages.INFO: 'alert-info',
    messages.SUCCESS: 'alert-success',
    messages.WARNING: 'alert-warning',
    messages.ERROR: 'alert-danger',
}

TEMPLATE_CONTEXT_PROCESSORS = (
    "django.contrib.auth.context_processors.auth",
    "django.core.context_processors.debug",
    "django.core.context_processors.i18n",
    "django.core.context_processors.media",
    "django.core.context_processors.static",
    "django.core.context_processors.tz",
    "django.contrib.messages.context_processors.messages",
    "fts_web.context_processors.testing_mode"
)

#Crispy Forms
CRISPY_TEMPLATE_PACK = 'bootstrap3'

TEST_RUNNER = "fts_web.tests.utiles.FTSenderDiscoverRunner"

#==============================================================================
# Import de `fts_web_settings_local`
#==============================================================================

try:
    from fts_web_settings_local import *
except ImportError as e:
    print "# "
    print "# ERROR"
    print "# "
    print "#   No se pudo importar el modulo"
    print "#       `fts_web_settings_local`"
    print "# "
    raise Exception("No se pudo importar fts_web_settings_local")

# ~~~~~ Check FTS_DIALPLAN_FILENAME

assert FTS_DIALPLAN_FILENAME is not None, \
    "Falta definir setting para FTS_DIALPLAN_FILENAME"

assert os.path.isabs(FTS_DIALPLAN_FILENAME), \
    "FTS_DIALPLAN_FILENAME debe ser un path absoluto"

if os.path.exists(FTS_DIALPLAN_FILENAME):
    assert not os.path.isdir(FTS_DIALPLAN_FILENAME), \
    "FTS_DIALPLAN_FILENAME es un directorio"

assert os.path.exists(os.path.dirname(FTS_DIALPLAN_FILENAME)), \
    "FTS_DIALPLAN_FILENAME: el directorio '{0}' no existe".format(
        os.path.dirname(FTS_DIALPLAN_FILENAME))

# ~~~~~ Check FTS_QUEUE_FILENAME

assert FTS_QUEUE_FILENAME is not None, \
    "Falta definir setting para FTS_QUEUE_FILENAME"

assert os.path.isabs(FTS_QUEUE_FILENAME), \
    "FTS_QUEUE_FILENAME debe ser un path absoluto"

if os.path.exists(FTS_QUEUE_FILENAME):
    assert not os.path.isdir(FTS_QUEUE_FILENAME), \
        "FTS_QUEUE_FILENAME es un directorio"

assert os.path.exists(os.path.dirname(FTS_QUEUE_FILENAME)), \
    "FTS_QUEUE_FILENAME: el directorio '{0}' no existe".format(
        os.path.dirname(FTS_QUEUE_FILENAME))

# ~~~~~ Check FTS_RELOAD_CMD

assert FTS_RELOAD_CMD is not None, \
    "Falta definir setting para FTS_RELOAD_CMD"

# ~~~~~ Check TMPL_FTS_AUDIO_CONVERSOR

assert TMPL_FTS_AUDIO_CONVERSOR is not None, \
    "Falta definir setting para TMPL_FTS_AUDIO_CONVERSOR"

assert "<INPUT_FILE>" in TMPL_FTS_AUDIO_CONVERSOR, \
    "Falta definir <INPUT_FILE> en TMPL_FTS_AUDIO_CONVERSOR"

assert "<OUTPUT_FILE>" in TMPL_FTS_AUDIO_CONVERSOR, \
    "Falta definir <OUTPUT_FILE> en TMPL_FTS_AUDIO_CONVERSOR"

# ~~~~~ Check TMPL_FTS_AUDIO_CONVERSOR

assert TMPL_FTS_AUDIO_CONVERSOR_EXTENSION is not None, \
    "Falta definir setting para TMPL_FTS_AUDIO_CONVERSOR_EXTENSION"

# ~~~~~ Check ASTERISK

for key in ('USERNAME', 'PASSWORD', 'HOST', 'PORT', 'CHANNEL_PREFIX',
    'LOCAL_CHANNEL', 'CONTEXT', 'EXTEN', 'PRIORITY', 'TIMEOUT',
    'HTTP_AMI_URL'):
    assert key in ASTERISK, \
        "Falta key '{0}' en configuracion de ASTERISK".format(key)
