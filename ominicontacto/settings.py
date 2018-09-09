# -*- coding: utf-8 -*-
# Copyright (C) 2018 Freetech Solutions

# This file is part of OMniLeads

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program.  If not, see http://www.gnu.org/licenses/.
#

"""
Django settings for ominicontacto project.

Generated by 'django-admin startproject' using Django 1.9.5.

For more information on this file, see
https://docs.djangoproject.com/en/1.9/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/1.9/ref/settings/
"""

import os
import subprocess

from django.contrib import messages

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/1.9/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
# SECRET_KEY = 's1+*bfrvb@=k@c&9=pm!0sijjewneu5p5rojil#q+!a2y&as-4'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = False

ALLOWED_HOSTS = []

# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'configuracion_telefonia_app',
    'crispy_forms',
    'compressor',
    'defender',
    'formtools',
    'ominicontacto_app',
    'reciclado_app',
    'reportes_app',
    'simple_history',
    'widget_tweaks',
]

# <ics>
INSTALLED_APPS += [
    'fts_web',
    'fts_daemon',
    'bootstrap3_datetime',
]
# </ics>

MIDDLEWARE_CLASSES = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.auth.middleware.SessionAuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'defender.middleware.FailedLoginMiddleware',
]


# django-compressor settings
COMPRESS_OFFLINE = True

STATICFILES_FINDERS = (
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
    # other finders..
    'compressor.finders.CompressorFinder',
)

ROOT_URLCONF = 'ominicontacto.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        # 'DIRS': [os.path.join(os.path.dirname(__file__),'templates')],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'ominicontacto.wsgi.application'

# Password hashers available
# https://docs.djangoproject.com/en/1.9/topics/auth/passwords/

PASSWORD_HASHERS = [
    'django.contrib.auth.hashers.PBKDF2PasswordHasher',
    'django.contrib.auth.hashers.BCryptSHA256PasswordHasher',
]

# Password validation
# https://docs.djangoproject.com/en/1.9/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

SESSION_EXPIRE_AT_BROWSER_CLOSE = True
SESSION_COOKIE_AGE = 600
SESSION_SAVE_EVERY_REQUEST = True
# Internationalization
# https://docs.djangoproject.com/en/1.9/topics/i18n/

LANGUAGE_CODE = 'es-ar'

TIME_ZONE = 'America/Argentina/Cordoba'

USE_I18N = True

USE_L10N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.9/howto/static-files/

STATIC_URL = '/static/'

MEDIA_URL = '/media/'

# STATICFILES_DIRS = [
#   os.path.join(BASE_DIR, "static"),
# ]

AUTH_USER_MODEL = 'ominicontacto_app.User'

# TEST_RUNNER = "ominicontacto_app.tests.utiles.ManagedModelTestRunner"
TEST_RUNNER = "fts_web.tests.utiles.FTSenderDiscoverRunner"
"""
FTSenderDiscoverRunner hereda de 'ominicontacto_app.tests.utiles.ManagedModelTestRunner', por eso
podemos usarlo sin problemas
"""

OML_TESTING_MODE = False

LOGIN_REDIRECT_URL = 'index'

OL_SIP_LIMITE_INFERIOR = 1000
OL_SIP_LIMITE_SUPERIOR = 3000


OL_NRO_TELEFONO_LARGO_MIN = 5
"""Largo minimo permitido de nros telefonicos"""

OL_NRO_TELEFONO_LARGO_MAX = 15
"""Largo maximo permitido de nros telefonicos"""

OL_MAX_CANTIDAD_CONTACTOS = 60000
"""Límite de contactos que pueden ser importados a la base de datos."""

SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

OML_DUMP_HTTP_AMI_RESPONSES = False

# ==============================================================================
# Settings de DEPLOY (para ser customizados en distintos deploys)
#     Nota: Los settings que siguen, pueden (y algunos DEBEN) ser modificados
#        en los distintos ambientes / deploys
# ==============================================================================

# ==============================================================================
# DEPLOY -> IP OMNILEADS
# ==============================================================================

OML_OMNILEADS_IP = None
"""IP donde se encuentra kamailio-debian

Ejemplo:
    OML_OMNILEADS_IP = "172.16.20.241"
"""

# ==============================================================================
# DEPLOY -> Asterisk
# ==============================================================================

OML_ASTERISK_HOSTNAME = None
OML_ASTERISK_REMOTEPATH = None
OML_SIP_FILENAME = None
OML_QUEUES_FILENAME = None
OML_BACKLIST_REMOTEPATH = None
OML_RUTAS_SALIENTES_FILENAME = None
"""Path completo (absoluto) al archivo donde se debe generar queues

Ejemplos:

.. code-block:: python

    OML_ASTERISK_HOSTNAME = "root@192.168.1.23"
    OML_ASTERISK_REMOTEPATH = "/etc/asterisk/"
    OML_SIP_FILENAME = "/etc/asterisk/sip_fts.conf"
    OML_QUEUES_FILENAME = "/etc/asterisk/queues_fts.conf"
    OML_BACKLIST_REMOTEPATH  = "/var/spool/asterisk/"
    OML_RUTAS_SALIENTES_FILENAME = "/etc/asterisk/oml_extensions_outr.conf"
"""

OML_RELOAD_CMD = None
"""Comando a ejecutar para hacer reload de Asterisk

Ejemplo:

.. code-block:: python

    OML_RELOAD_CMD = ["/usr/bin/asterisk", "-x", "reload"]
"""

ASTERISK = {
    'USERNAME': None,  # Usuario para AMI
    'PASSWORD': None,  # Password para usuario para AMI
    'HTTP_AMI_URL': None,
    'DIAL_URL': None,
    # URL usado por Daemon p/acceder a Asterisk AMI via HTTP
    # Ej:
    #    "http://1.2.3.4:7088"
}

TMPL_OML_AUDIO_CONVERSOR = None
"""Comando para convertir audios (wav a gsm)

Ejemplos:

.. code-block:: python

    TMPL_OML_AUDIO_CONVERSOR = ["sox", "<INPUT_FILE>", "<OUTPUT_FILE>"]

Para transformar WAV (cualquier formato) -> WAV (compatible con Asterisk):

.. code-block:: python

    TMPL_OML_AUDIO_CONVERSOR = ["sox", "-t", "wav", "<INPUT_FILE>",
        "-r", "8k", "-c", "1", "-e", "signed-integer",
        "-t", "wav", "<OUTPUT_FILE>"
    ]

"""

TMPL_OML_AUDIO_CONVERSOR_EXTENSION = None
"""Extension a usar para archivo generado por `TMPL_OML_AUDIO_CONVERSOR`

Ejemplo: `.wav` (con el . incluido):  el archivo `<OUTPUT_FILE>`
tendra la extension `.wav`
"""

OML_AUDIO_PATH_ASTERISK = None
"""Directory donde se guardan los audios de asterisk en el server de asterisk

Ejemplo:
    OML_WOMBAT_FILENAME = "/var/lib/asterisk/sounds/oml/"
"""

# ==============================================================================
# DEPLOY -> KAMAILIO
# ==============================================================================

OML_KAMAILIO_IP = None
"""IP donde se encuentra kamailio-debian

Ejemplo:
    OML_KAMAILIO_IP = "172.16.20.219/255.255.255.255"
"""

# ==============================================================================
# URL DE GRABACIONES DE ELASTIX
# ==============================================================================

OML_GRABACIONES_URL = None
"""Url de donde buscar las grabaciones de las llamadas

Ejemplo:
    OML_GRABACIONES_URL = "http://172.16.20.222/grabaciones"
"""

# ==============================================================================
# URL DE SUPERVISION
# ==============================================================================

OML_SUPERVISION_URL = None
"""Url de donde se encuentra la supervision

Ejemplo:
    OML_SUPERVISION_URL = "http://172.16.20.222:8090/Omnisup/index.php"
"""

# ==============================================================================
# WOMBAT Config
# ==============================================================================

OML_WOMBAT_URL = None
"""Url de discador de Wombat

Ejemplo:
    OML_WOMBAT_URL = "http://172.16.20.222/wombat"
"""


OML_WOMBAT_FILENAME = None
"""Directory donde se guardan los json de config de wombat

Ejemplo:
    OML_WOMBAT_FILENAME = "/home/freetech/"
"""

OML_WOMBAT_USER = None
OML_WOMBAT_PASSWORD = None
"""
User y password por el cual se conectan con la api de WOMBAT DIALER
Ejemplo:
    OML_WOMBAT_USER = "user_test"
    OML_WOMBAT_PASSWORD = "user123"
"""

CALIFICACION_REAGENDA = None


#==============================================================================
# ***ICS*** -> Settings INTERNOS (NO son para customizar el deploy)
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

FTS_NOMBRE_TABLA_CDR = 'fts_cdr'
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
# ***ICS*** -> Django
#==============================================================================

MIDDLEWARE_CLASSES += [
    'fts_web.middleware.ReportErrorMiddleware',
]

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

# ROOT_URLCONF = 'fts_web.urls'

# WSGI_APPLICATION = 'fts_web.wsgi.application'

# LANGUAGE_CODE = 'es-ar'
# TIME_ZONE = 'America/Argentina/Cordoba'
# USE_I18N = True
# USE_L10N = True
# USE_TZ = True

# STATIC_URL = '/static/'
# MEDIA_URL = '/media/'
# LOGIN_URL = "logueo"
# LOGOUT_URL = "deslogueo"
# LOGIN_REDIRECT_URL = '/'


#==============================================================================
# ***ICS*** -> Crispy Forms
#==============================================================================

CRISPY_TEMPLATE_PACK = 'bootstrap3'

# Bootstrap friendly
MESSAGE_TAGS = {
    messages.DEBUG: 'alert-info',
    messages.INFO: 'alert-info',
    messages.SUCCESS: 'alert-success',
    messages.WARNING: 'alert-warning',
    messages.ERROR: 'alert-danger',
}


#==============================================================================
# ***ICS*** -> Celery
#==============================================================================

# Por que 475? Parecido a FTS :-P
BROKER_URL = 'redis://127.0.0.1/3'

CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'


#==============================================================================
# ***ICS*** -> Settings de DEPLOY (para ser customizados en distintos deploys)
#     Nota: Los settings que siguen, pueden (y algunos DEBEN) ser modificados
#        en los distintos ambientes / deploys
#==============================================================================

#==============================================================================
# ***ICS*** -> DEPLOY -> Asterisk
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
# ***ICS*** -> DEPLOY -> Daemon
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
# ***ICS*** -> DEPLOY -> Varios
#==============================================================================

# ASTERISK = {
#     #'HOST': None,
#     #'PORT': None,
#     #'LOCAL_CHANNEL': None,
#     #'EXTEN': None,
#     #'PRIORITY': None,
#     'USERNAME': None,  # Usuario para AMI
#     'PASSWORD': None,  # Password para usuario para AMI
#     'HTTP_AMI_URL': None,
#         # URL usado por Daemon p/acceder a Asterisk AMI via HTTP
#         # Ej:
#         #    "http://1.2.3.4:7088"
#     'DIAL_URL': None,  # URL de Dial(). Debe contener '${NumberToCall}'
#         # URL a pasar a app. Dial()
#         # Ej:
#         #    "IAX2/1.2.3.4/${NumberToCall}"
# }
# """Configuracion para interactuar con Asterisk"""

FTS_BASE_DATO_CONTACTO_DUMP_PATH = None  #@IgnorePep8
"""
Path completo (absoluto) al dir donde se debe generar los dumps de la
depuración de BaseDatoContacto.
"""


#==============================================================================
# ***ICS*** -> DEPLOY -> REPORTE SMS
#==============================================================================

FTS_REPORTE_SMS_URL = None
"""URL donde se encuentran los reportes sms

Ej: http://172.20.2.249:9088/reporte_sms/REPORTE_SMS
"""

FTS_LIMITE_GLOBAL_DE_CHIPS = 10
"""Cantidad maxima 'global' de chips para usar, en conjunto de todas
las campañas de sms"""

#==============================================================================
# ***ICS*** -> DEMONIO SMS: MODEMS ó GATEWAY
#==============================================================================

FTS_SMS_UTILIZADO = 'modem'


























# ==============================================================================
# Import de `ics_settings_local` (EX: `fts_web_settings_local`)
# ==============================================================================

try:
    from ics_settings_local import *
except ImportError as e:
    print "# "
    print "# ERROR"
    print "# "
    print "#   No se pudo importar el modulo"
    print "#       `ics_settings_local`"
    print "#       (antes se llamaba `fts_web_settings_local`)"
    print "# "
    raise Exception("No se pudo importar 'ics_settings_local' (antes se llamaba 'fts_web_settings_local')")


# ==============================================================================
# Import de `oml_settings_local`
# ==============================================================================

try:
    from oml_settings_local import *
    # definir LOCAL_APPS en oml_settings_local, para insertar plugins de django que
    # sólo serán usados en ambientes de desarrollo y de testing, si no se tienen plugins
    # dejar LOCAL_APPS = []
    INSTALLED_APPS += LOCAL_APPS

    if DJANGO_DEBUG_TOOLBAR:
        MIDDLEWARE_CLASSES += [
            'debug_toolbar.middleware.DebugToolbarMiddleware',
        ]
except ImportError as e:
    print "# "
    print "# ERROR"
    print "# "
    print "#   No se pudo importar el modulo"
    print "#       `oml_settings_local`"
    print "# "
    raise Exception("No se pudo importar oml_settings_local")

# ~~~~~ Check OML_ASTERISK_HOSTNAME

assert OML_ASTERISK_HOSTNAME is not None, \
    "Falta definir setting para OML_ASTERISK_HOSTNAME"

# ~~~~~ Check OML_ASTERISK_REMOTEPATH

assert OML_ASTERISK_REMOTEPATH is not None, \
    "Falta definir setting para OML_ASTERISK_REMOTEPATH"

# ~~~~~ Check OML_SIP_FILENAME

assert OML_SIP_FILENAME is not None, \
    "Falta definir setting para OML_SIP_FILENAME"

# ~~~~~ Check OML_QUEUES_FILENAME

assert OML_QUEUES_FILENAME is not None, \
    "Falta definir setting para OML_QUEUES_FILENAME"

# ~~~~~ Check ASTERISK

for key in ('AMI_USERNAME', 'AMI_PASSWORD', 'HTTP_AMI_URL'):
    assert key in ASTERISK, \
        "Falta key '{0}' en configuracion de ASTERISK".\
        format(key)
    assert ASTERISK[key] is not None, \
        "Falta key '{0}' en configuracion de ASTERISK".\
        format(key)

# ~~~~~ Check OML_RELOAD_CMD

assert OML_RELOAD_CMD is not None, \
    "Falta definir setting para OML_RELOAD_CMD"


# ~~~~~ Check OML_GRABACIONES_URL

assert OML_GRABACIONES_URL is not None, \
    "Falta definir setting para OML_GRABACIONES_URL"

# ~~~~~ Check OML_GRABACIONES_URL

assert OML_SUPERVISION_URL is not None, \
    "Falta definir setting para OML_SUPERVISION_URL"

# ~~~~~ Check OML_KAMAILIO_IP

assert OML_KAMAILIO_IP is not None, \
    "Falta definir setting para OML_KAMAILIO_IP"

# ~~~~~ Check OML_WOMBAT_URL

assert OML_WOMBAT_URL is not None, \
    "Falta definir setting para OML_WOMBAT_URL"

# ~~~~~ Check OML_WOMBAT_FILENAME

assert OML_WOMBAT_FILENAME is not None, \
    "Falta definir setting para OML_WOMBAT_FILENAME"

# ~~~~~ Check OML_RUTAS_SALIENTES_FILENAME

assert OML_RUTAS_SALIENTES_FILENAME is not None, \
    "Falta definir setting para OML_RUTAS_SALIENTES_FILENAME"

# ~~~~~ Check OML_WOMBAT_USER

assert OML_WOMBAT_USER is not None, \
    "Falta definir setting para OML_WOMBAT_USER"

# ~~~~~ Check OML_WOMBAT_PASSWORD

assert OML_WOMBAT_PASSWORD is not None, \
    "Falta definir setting para OML_WOMBAT_PASSWORD"


# ~~~~~ Check OML_OMNILEADS_IP

assert OML_OMNILEADS_IP is not None, \
    "Falta definir setting para OML_OMNILEADS_IP"


# ~~~~~ Check OML_BACKLIST_REMOTEPATH

assert OML_BACKLIST_REMOTEPATH is not None, \
    "Falta definir setting para OML_BACKLIST_REMOTEPATH"


# ~~~~~ Check TMPL_OML_AUDIO_CONVERSOR

assert TMPL_OML_AUDIO_CONVERSOR is not None, \
    "Falta definir setting para TMPL_OML_AUDIO_CONVERSOR"

assert "<INPUT_FILE>" in TMPL_OML_AUDIO_CONVERSOR, \
    "Falta definir <INPUT_FILE> en TMPL_OML_AUDIO_CONVERSOR"

assert "<OUTPUT_FILE>" in TMPL_OML_AUDIO_CONVERSOR, \
    "Falta definir <OUTPUT_FILE> en TMPL_OML_AUDIO_CONVERSOR"

# 3 elementos como minimo: (1) comando (2/3) INPUT/OUTPUT
assert len(TMPL_OML_AUDIO_CONVERSOR) >= 3, \
    "TMPL_OML_AUDIO_CONVERSOR debe tener al menos 3 elementos"

ret = subprocess.call('which {0} > /dev/null 2> /dev/null'.format(
    TMPL_OML_AUDIO_CONVERSOR[0]), shell=True)

assert ret == 0, "No se ha encontrado el ejecutable configurado " +\
    "en TMPL_OML_AUDIO_CONVERSOR: '{0}'".format(TMPL_OML_AUDIO_CONVERSOR[0])

# ~~~~~ Check TMPL_OML_AUDIO_CONVERSOR

assert TMPL_OML_AUDIO_CONVERSOR_EXTENSION is not None, \
    "Falta definir setting para TMPL_OML_AUDIO_CONVERSOR"

# ~~~~~ Check ASTERISK_AUDIO_PATH

assert ASTERISK_AUDIO_PATH is not None, \
    "Falta definir setting para ASTERISK_AUDIO_PATH"

# ~~~~~ Check OML_AUDIO_FOLDER

assert OML_AUDIO_FOLDER is not None, \
    "Falta definir setting para OML_AUDIO_FOLDER"

# Una vez que tengo ASTERISK_AUDIO_PATH y OML_AUDIO_FOLDER puedo calcular OML_AUDIO_PATH_ASTERISK
OML_AUDIO_PATH_ASTERISK = ASTERISK_AUDIO_PATH + OML_AUDIO_FOLDER

# ~~~~~ Check CALIFICACION_REAGENDA

assert CALIFICACION_REAGENDA is not None, \
    "Falta definir setting para CALIFICACION_REAGENDA"


#==============================================================================
# ***ICS*** -> Import de `fts_web_settings_local_customizations`
#==============================================================================

# try:
#     from fts_web_settings_local_customizations import *
# except ImportError as e:
#     print("# WARN: no se pudo importar el modulo "
#         "'fts_web_settings_local_customizations'")

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

# assert os.path.exists(os.path.dirname(FTS_DIALPLAN_FILENAME)), \
#    "FTS_DIALPLAN_FILENAME: el directorio '{0}' no existe".format(
#        os.path.dirname(FTS_DIALPLAN_FILENAME))

# ~~~~~ Check FTS_QUEUE_FILENAME

assert FTS_QUEUE_FILENAME is not None, \
    "Falta definir setting para FTS_QUEUE_FILENAME"

assert os.path.isabs(FTS_QUEUE_FILENAME), \
    "FTS_QUEUE_FILENAME debe ser un path absoluto"

if os.path.exists(FTS_QUEUE_FILENAME):
    assert not os.path.isdir(FTS_QUEUE_FILENAME), \
        "FTS_QUEUE_FILENAME es un directorio"

# assert os.path.exists(os.path.dirname(FTS_QUEUE_FILENAME)), \
#    "FTS_QUEUE_FILENAME: el directorio '{0}' no existe".format(
#        os.path.dirname(FTS_QUEUE_FILENAME))

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
## y por lo tanto, migrate, etc. no funcionan.

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
