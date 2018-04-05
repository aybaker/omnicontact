# -*- coding: utf-8 -*-

"""
Settings básicos de Django para la aplicación FTS.

For more information on this file, see
https://docs.djangoproject.com/en/1.6/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/1.6/ref/settings/

"""

from __future__ import unicode_literals

import os
import subprocess

from django.contrib import messages


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

FTS_ASTERISK_HTTP_CLIENT = "fts_daemon.asterisk_ami_http.AsteriskHttpClient"

FTS_PROGRAMAR_CAMPANA_FUNC = "_programar_campana_sqlite"

FTS_EVENTOS_FINALIZADORES = [
    "EVENTO_ASTERISK_DIALPLAN_CAMPANA_INICIADO",
    #    "EVENTO_ASTERISK_DIALPLAN_CAMPANA_FINALIZADO",
    #    "EVENTO_ASTERISK_DIALPLAN_CAMPANA_ERR_T",
    #    "EVENTO_ASTERISK_DIALPLAN_CAMPANA_ERR_I",
]

FTS_DUMP_HTTP_AMI_RESPONSES = False
"""Si se hará un DUMP de cada respuesta, cada XML recibido,
a un archivo en el directorio temporal."""

FTS_SETTING_CUSTOMIZERS = []

FTS_MAX_CANTIDAD_CONTACTOS = 60000
"""Límite de contactos que pueden ser importados a la base de datos."""

FTS_MARGEN_DIFERENCIA_DURACION_LLAMADAS = 0.05
"""Margen en porcentaje que diferencia que el mensaje de una campana fue
   escuchado completo o no. Se aplica sobre la duración de las llamadas."""

FTS_TTS_GOOGLE = 'google'
FTS_TTS_SWIFT = 'swift'
FTS_TTS_DISPONIBLES = [
    FTS_TTS_GOOGLE,
    FTS_TTS_SWIFT,
]

FTS_TTS_UTILIZADO = FTS_TTS_GOOGLE
"""Sistema de tts utilizado por asterisk. Por defecto el de google."""

#Crispy Forms
CRISPY_TEMPLATE_PACK = 'bootstrap3'

TEST_RUNNER = "fts_web.tests.utiles.FTSenderDiscoverRunner"

# Asterisk

FTS_ASTERISK_DIALPLAN_LOCAL_CHANNEL = "Local/{contactoId}-{numberToCall}-{intento}@FTS_local_campana_{campanaId}"  #@IgnorePep8

FTS_ASTERISK_DIALPLAN_EXTEN = "fts-{contactoId}-{numberToCall}-{intento}"

FTS_ASTERISK_DIALPLAN_PRIORITY = 1

FTS_FDCD_LOOP_SLEEP = 60 * 10
"""Finalizador De Campanas Daemon - Espera entre reejecucion de loop.
Default: 10 minutos
"""

FTS_FDCD_MAX_LOOP_COUNT = 0
"""Finalizador De Campanas Daemon - Cantidad máxima de loops a ejecutar.

Default: 0 (ejecuta loop indefinidamente)
"""

FTS_FDCD_INITIAL_WAIT = 20.0
"""Finalizador De Campanas Daemon - Espera inicial, antes iniciar el loop

Default: 20.0 (inicia ejecucion del loop despues de 20 segundos)
"""

FTS_NOMBRE_TABLA_CDR = 'cdr'
"""
Nombre personalizado de la tabla  CDR de Asterisk.
"""

#FTS_JOIN_TIMEOUT_MARGIN = 5
#"""Cuantos segundos esperar (mas alla del timeout para ORIGINATE)
#para que el proceso hijo termine
#"""

AUDIOS_PARA_MESES = [
    "enero",
    "febrero",
    "marzo",
    "abril",
    "mayo",
    "junio",
    "julio",
    "agosto",
    "setiembre",
    "octubre",
    "noviembre",
    "diciembre",
]
"""Archivos de audio a utilizar en el dialpla para los TTS de tipo fecha"""

#==============================================================================
# Celery
#==============================================================================

# Por que 475? Parecido a FTS :-P
BROKER_URL = 'redis://127.0.0.1/3'

CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'

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
    'fts_daemon',
    'crispy_forms',
    'bootstrap3_datetime',
)

MIDDLEWARE_CLASSES = (
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'fts_web.middleware.ReportErrorMiddleware',
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

LOGIN_URL = "logueo"
LOGOUT_URL = "deslogueo"
LOGIN_REDIRECT_URL = '/'

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
    "fts_web.context_processors.testing_mode",
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

Ejemplo: `.wav` (con el . incluido):  el archivo `<OUTPUT_FILE>`
tendra la extension `.wav`
"""

FTS_ASTERISK_CONFIG_CHECK_AUDIO_FILE_EXISTS = True

#==============================================================================
# DEPLOY -> Daemon
#==============================================================================

FTS_AGI_DAEMON_HOST = "127.0.0.1"
"""Host o IP a utilizar desde Asterisk para que la app AGI()
pueda llamar al daemon AGI
"""

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

FTS_DAEMON_ORIGINATES_PER_SECOND = 1.0 / 3.0
"""Cuantos originates se pueden realizar por segundos. Soporta valores < 1.0.
Debe ser float, y >= 0.0. Si vale 0.0, implica que no hay limite.
"""

FTS_LIMITE_GLOBAL_DE_CANALES = 100
"""Cantidad maxima 'global' de canales para usar, en conjunto de todas
las campañas"""

FTS_ESPERA_POR_LIMITE_GLOBAL_DE_CANALES = 3.0
"""Tiempo a esperar cuando se alcanza el limite global de canales.
Debe ser float. Para ser usado en sleep.
"""

FTS_DAEMON_STATS_VALIDEZ = 5
"""Por cuantos segundos se consideran validios las estadisticas
obtenidas del cache. Si la estadistica obtenida desde el cache
fue creada hace mas de `FTS_DAEMON_STATS_VALIDEZ` segundos,
se muestra un WARN, avisando que las estadisticas son viejas."""

FTS_NRO_TELEFONO_LARGO_MIN = 10
"""Largo minimo permitido de nros telefonicos"""

FTS_NRO_TELEFONO_LARGO_MAX = 13
"""Largo maximo permitido de nros telefonicos"""

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
    'USERNAME': None,  # Usuario para AMI
    'PASSWORD': None,  # Password para usuario para AMI
    'HTTP_AMI_URL': None,
        # URL usado por Daemon p/acceder a Asterisk AMI via HTTP
        # Ej:
        #    "http://1.2.3.4:7088"
    'DIAL_URL': None,  # URL de Dial(). Debe contener '${NumberToCall}'
        # URL a pasar a app. Dial()
        # Ej:
        #    "IAX2/1.2.3.4/${NumberToCall}"
}
"""Configuracion para interactuar con Asterisk"""

FTS_BASE_DATO_CONTACTO_DUMP_PATH = None  #@IgnorePep8
"""
Path completo (absoluto) al dir donde se debe generar los dumps de la
depuración de BaseDatoContacto.
"""


#==============================================================================
# DEPLOY -> REPORTE SMS
#==============================================================================

FTS_REPORTE_SMS_URL = None
"""URL donde se encuentran los reportes sms

Ej: http://172.20.2.249:9088/reporte_sms/REPORTE_SMS
"""

FTS_LIMITE_GLOBAL_DE_CHIPS = 10
"""Cantidad maxima 'global' de chips para usar, en conjunto de todas
las campañas de sms"""

#==============================================================================
# DEMONIo SMS: MODEMS ó GATEWAY
#==============================================================================

FTS_SMS_UTILIZADO = 'modem'

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

#==============================================================================
# Import de `fts_web_settings_local_customizations`
#==============================================================================

try:
    from fts_web_settings_local_customizations import *
except ImportError as e:
    print("# WARN: no se pudo importar el modulo "
        "'fts_web_settings_local_customizations'")

# ~~~~~ Check FTS_TTS_UTILIZADO

assert FTS_TTS_UTILIZADO is not None, \
    "Falta definir setting para FTS_TTS_UTILIZADO"

assert FTS_TTS_UTILIZADO in FTS_TTS_DISPONIBLES, \
    "El TTS: {0} definido en setting no es uno disponible.".format(
        FTS_TTS_UTILIZADO)

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

# 3 elementos como minimo: (1) comando (2/3) INPUT/OUTPUT
assert len(TMPL_FTS_AUDIO_CONVERSOR) >= 3, \
    "TMPL_FTS_AUDIO_CONVERSOR debe tener al menos 3 elementos"

ret = subprocess.call('which {0} > /dev/null 2> /dev/null'.format(
    TMPL_FTS_AUDIO_CONVERSOR[0]), shell=True)

assert ret == 0, "No se ha encontrado el ejecutable configurado " +\
    "en TMPL_FTS_AUDIO_CONVERSOR: '{0}'".format(TMPL_FTS_AUDIO_CONVERSOR[0])

# ~~~~~ Check TMPL_FTS_AUDIO_CONVERSOR

assert TMPL_FTS_AUDIO_CONVERSOR_EXTENSION is not None, \
    "Falta definir setting para TMPL_FTS_AUDIO_CONVERSOR_EXTENSION"

# ~~~~~ Check ASTERISK

for key in ('USERNAME', 'PASSWORD', 'HTTP_AMI_URL', 'DIAL_URL'):
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


# ~~~~~ Check FTS_DAEMON_ORIGINATES_PER_SECOND

assert type(FTS_DAEMON_ORIGINATES_PER_SECOND) == float, \
    "FTS_DAEMON_ORIGINATES_PER_SECOND debe ser float"

assert type(FTS_DAEMON_ORIGINATES_PER_SECOND) >= 0.0, \
    "FTS_DAEMON_ORIGINATES_PER_SECOND debe >= 0.0"


# ~~~~~ UWSGI_CACHE_FALLBACK

UWSGI_CACHE_FALLBACK = True

## Si lo desactivamos, los comandos ejecutados con 'manage.py'
## fallan! (porque no son ejecutados en uWSGI, doh)
## y por lo tanto, syncdb, migrate, etc. no funcionan.

# ~~~~~ Customizators

for customizator_func in FTS_SETTING_CUSTOMIZERS:
    customizator_func(locals())

# ~~~~~ Check FTS_BASE_DATO_CONTACTO_DUMP_PATH

assert FTS_BASE_DATO_CONTACTO_DUMP_PATH is not None, \
    "Falta definir setting para FTS_BASE_DATO_CONTACTO_DUMP_PATH"

assert os.path.isabs(FTS_BASE_DATO_CONTACTO_DUMP_PATH), \
    "FTS_BASE_DATO_CONTACTO_DUMP_PATH debe ser un path absoluto"

assert os.path.exists(os.path.dirname(FTS_BASE_DATO_CONTACTO_DUMP_PATH)), \
    "FTS_BASE_DATO_CONTACTO_DUMP_PATH: el directorio '{0}' no existe".format(
        os.path.dirname(FTS_BASE_DATO_CONTACTO_DUMP_PATH))


#==============================================================================
# Variables de entorno usadas
#==============================================================================
#
# FTS_RUN_ASTERISK_TEST: si esta definida, se ejecutaran los tests
#    que requieren Asterisk
#
