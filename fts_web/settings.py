# -*- coding: utf-8 -*-

"""
Settings básicos de Django para la aplicación FTS.

For more information on this file, see
https://docs.djangoproject.com/en/1.6/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/1.6/ref/settings/

"""

from __future__ import unicode_literals

from django.contrib import messages
import os


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/1.6/howto/deployment/checklist/

DEBUG = False

TEMPLATE_DEBUG = False

#==============================================================================
# Settings INTERNOS (NO son para customizar el deploy)
#  Nota: estas variables NO deberian ser modificadas
#    en `fts_web_settings_local`
#==============================================================================

FTS_ENHANCED_URLS = False
"""Si FTS_ENHANCED_URLS value true, se sirve /media, /static, etc.
En produccion deberia ser FALSE
"""

FTS_STOP_ON_SELENIUM_ASSERT_ERROR = False
"""Usado en tests de Selenium, en conjunto al metodo `assertTrueSelenium()`.
Si es verdadero y el assert falla, la ejecucion del test es pausada, para
poder ver el mensaje en el navegador.

Ver `assertTrueSelenium()` para mas informacion
"""

FTS_TESTING_MODE = False
"""Esta variable vale `True` cuando se estan ejecutando los test."""

#FTS_ORIGINATE_SERVICE_CLASS = "fts_daemon.asterisk_originate."\
#    "OriginateServiceProcess"

FTS_ASTERISK_HTTP_CLIENT = "fts_daemon.asterisk_ami_http.AsteriskHttpClient"

FTS_PROGRAMAR_CAMPANA_FUNC = "_programar_campana_sqlite"

FTS_EVENTOS_FINALIZADORES = [
    "EVENTO_ASTERISK_DIALPLAN_CAMPANA_INICIADO",
    "EVENTO_ASTERISK_DIALPLAN_CAMPANA_FINALIZADO",
    "EVENTO_ASTERISK_DIALPLAN_CAMPANA_ERR_T",
    "EVENTO_ASTERISK_DIALPLAN_CAMPANA_ERR_I",
]

FTS_DUMP_HTTP_AMI_RESPONSES = False
"""Si se hará un DUMP de cada respuesta, cada XML recibido,
a un archivo en el directorio temporal."""

FTS_SETTING_CUSTOMIZERS = []

#Crispy Forms
CRISPY_TEMPLATE_PACK = 'bootstrap3'

TEST_RUNNER = "fts_web.tests.utiles.FTSenderDiscoverRunner"

# Asterisk

FTS_ASTERISK_DIALPLAN_LOCAL_CHANNEL = "Local/{contactoId}-{numberToCall}@FTS_local_campana_{campanaId}"  #@IgnorePep8

FTS_ASTERISK_DIALPLAN_EXTEN = "fts{contactoId}"

FTS_ASTERISK_DIALPLAN_PRIORITY = 1

#FTS_JOIN_TIMEOUT_MARGIN = 5
#"""Cuantos segundos esperar (mas alla del timeout para ORIGINATE)
#para que el proceso hijo termine
#"""

#==============================================================================
# Django
#==============================================================================

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










#==============================================================================
# Settings de DEPLOY (para ser customizados en distintos deploys)
#     Nota: Los settings que siguen, pueden (y algunos DEBEN) ser modificados
#        en los distintos ambientes / deploys
#==============================================================================


#==============================================================================
# DEPLOY -> Asterisk
#==============================================================================

FTS_DIALPLAN_FILENAME = None  #@IgnorePep8
"""Path completo (absoluto) al archivo donde se debe generar el dialplan

Ejemplos:

.. code-block:: python

    FTS_DIALPLAN_FILENAME = "/opt/asterisk-11/etc/extensions-ftsender.conf"
    FTS_DIALPLAN_FILENAME = "/opt/asterisk-11/etc/ftsender/extensions.conf"
"""

FTS_QUEUE_FILENAME = None
"""Path completo (absoluto) al archivo donde se debe generar queues

Ejemplos:

.. code-block:: python

    FTS_QUEUE_FILENAME = "/opt/asterisk-11/etc/queues-ftsender.conf"
    FTS_QUEUE_FILENAME = "/opt/asterisk-11/etc/ftsender/queues.conf"
"""

FTS_RELOAD_CMD = None
"""Comando a ejecutar para hacer reload de Asterisk

Ejemplo:

.. code-block:: python

    FTS_RELOAD_CMD = ["/usr/bin/asterisk", "-x", "reload"]
"""

TMPL_FTS_AUDIO_CONVERSOR = None
"""Comando para convertir audios (wav a gsm)

Ejemplos:

.. code-block:: python

    TMPL_FTS_AUDIO_CONVERSOR = ["sox", "<INPUT_FILE>", "<OUTPUT_FILE>"]

Para transformar WAV (cualquier formato) -> WAV (compatible con Asterisk):

.. code-block:: python

    TMPL_FTS_AUDIO_CONVERSOR = ["sox", "-t", "wav", "<INPUT_FILE>",
        "-r", "8k", "-c", "1", "-e", "signed-integer",
        "-t", "wav", "<OUTPUT_FILE>"
    ]

"""

TMPL_FTS_AUDIO_CONVERSOR_EXTENSION = None
"""Extension a usar para archivo generado por `TMPL_FTS_AUDIO_CONVERSOR`

Ejemplo: *.wav* (con el . incluido):  el archivo `<OUTPUT_FILE>`
tendra la extension `.wav`
"""

FTS_ASTERISK_CONFIG_CHECK_AUDIO_FILE_EXISTS = True

#==============================================================================
# DEPLOY -> Daemon
#==============================================================================

FTS_FAST_AGI_DAEMON_PROXY_URL = None
"""URL donde `fastagi_daemon` realizará el request.
Debe ser el URL para acceder a Django (SIN el / final)

Ej: http://localhost:8080
"""

FTS_FAST_AGI_DAEMON_BIND = "0.0.0.0"
"""Bind de fast agi daemon"""

FTS_DAEMON_SLEEP_SIN_TRABAJO = 2
"""Cuantos segundos se esperará en el loop del daemon si no hay más
trabajo por realizar
"""

FTS_DAEMON_SLEEP_LIMITE_DE_CANALES = 2
"""Cuantos segundos se esperará en el loop del daemon si todos las
campañas llegaron al límite de uso de canales
"""

#FTS_MARGEN_FINALIZACION_CAMPANA = 600
#"""Cuanto tiempo debe pasar (despues del ultimo evento) para
#finalizar una campana
#"""

#==============================================================================
# DEPLOY -> Varios
#==============================================================================

ASTERISK = {
    #'HOST': None,
    #'PORT': None,
    #'LOCAL_CHANNEL': None,
    #'EXTEN': None,
    #'PRIORITY': None,
    'USERNAME': None, # Usuario para AMI
    'PASSWORD': None, # Password para usuario para AMI
    'HTTP_AMI_URL': None, # URL para acceder a AMI
}
"""Configuracion para interactuar con Asterisk"""


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

for key in ('USERNAME', 'PASSWORD', 'HTTP_AMI_URL'):
    assert key in ASTERISK, \
        "Falta key '{0}' en configuracion de ASTERISK".format(key)
    assert ASTERISK[key] is not None, \
        "Falta key '{0}' en configuracion de ASTERISK".format(key)

for key in ('CONTEXT', 'CHANNEL_PREFIX', 'HOST', 'PORT', 'LOCAL_CHANNEL',
    'EXTEN', 'PRIORITY', 'TIMEOUT'):
    assert key not in ASTERISK, \
        "ASTERISK['{0}'] ya no debe incluirse, porque no se usa".format(key)

ASTERISK['LOCAL_CHANNEL'] = FTS_ASTERISK_DIALPLAN_LOCAL_CHANNEL
ASTERISK['EXTEN'] = FTS_ASTERISK_DIALPLAN_EXTEN
ASTERISK['PRIORITY'] = FTS_ASTERISK_DIALPLAN_PRIORITY

assert FTS_FAST_AGI_DAEMON_PROXY_URL is not None, \
    "Falta definir setting para FTS_FAST_AGI_DAEMON_PROXY_URL"


# ~~~~~ Customizators

for customizator_func in FTS_SETTING_CUSTOMIZERS:
    customizator_func(locals())


#==============================================================================
# Variables de entorno usadas
#==============================================================================
#
# FTS_RUN_ASTERISK_TEST: si esta definida, se ejecutaran los tests
#    que requieren Asterisk
#
