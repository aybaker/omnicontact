# -*- coding: utf-8 -*-
"""
Django settings for fts_web project.

For more information on this file, see
https://docs.djangoproject.com/en/1.6/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/1.6/ref/settings/
"""
from django.contrib import messages

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
import os
BASE_DIR = os.path.dirname(os.path.dirname(__file__))

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/1.6/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'uqe^e2bg^ys2ae&5*jw414_r!m*r7+6-mb%(d3hv+xy4hv^38l'

#SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

TEMPLATE_DEBUG = True

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
"""
TMPL_FTS_AUDIO_CONVERSOR = None


ALLOWED_HOSTS = []


# Application definition

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


# Internationalization
# https://docs.djangoproject.com/en/1.6/topics/i18n/

LANGUAGE_CODE = 'es-ar'

TIME_ZONE = 'America/Argentina/Cordoba'

USE_I18N = True

USE_L10N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.6/howto/static-files/

STATIC_URL = '/static/'

#Media files
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

TEST_RUNNER = "fts_web.tests.FTSenderDiscoverRunner"

try:
    from fts_web.settings_local import *
except ImportError as e:
    import warnings
    warnings.warn("Couldn't import from 'fts_web.local_settings': {0}".format(
        e.args[0]), stacklevel=0)

# Check FTS_DIALPLAN_FILENAME

assert FTS_DIALPLAN_FILENAME is not None, \
    "Falta definir setting para FTS_DIALPLAN_FILENAME"

assert os.path.isabs(FTS_DIALPLAN_FILENAME), \
    "FTS_DIALPLAN_FILENAME debe ser un path absoluto"

if os.path.exists(FTS_DIALPLAN_FILENAME):
    assert not os.path.isdir(FTS_DIALPLAN_FILENAME, \
        "FTS_DIALPLAN_FILENAME es un directorio")

# Check FTS_QUEUE_FILENAME

assert FTS_QUEUE_FILENAME is not None, \
    "Falta definir setting para FTS_QUEUE_FILENAME"

assert os.path.isabs(FTS_QUEUE_FILENAME), \
    "FTS_QUEUE_FILENAME debe ser un path absoluto"

if os.path.exists(FTS_QUEUE_FILENAME):
    assert not os.path.isdir(FTS_QUEUE_FILENAME, \
        "FTS_QUEUE_FILENAME es un directorio")

# Check FTS_RELOAD_CMD

assert FTS_RELOAD_CMD is not None, \
    "Falta definir setting para FTS_RELOAD_CMD"

# Check TMPL_FTS_AUDIO_CONVERSOR

assert TMPL_FTS_AUDIO_CONVERSOR is not None, \
    "Falta definir setting para TMPL_FTS_AUDIO_CONVERSOR"

assert "<INPUT_FILE>" in TMPL_FTS_AUDIO_CONVERSOR, \
    "Falta definir <INPUT_FILE> en TMPL_FTS_AUDIO_CONVERSOR"

assert "<OUTPUT_FILE>" in TMPL_FTS_AUDIO_CONVERSOR, \
    "Falta definir <OUTPUT_FILE> en TMPL_FTS_AUDIO_CONVERSOR"
