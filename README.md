Entorno de desarrollo
=====================

El entorno utilizado para desarrollo es Ubuntu 14.04.

El sistema debe ser desarrollado usando Python 2.6 y virtualenv.

Para la instalación de algunos paquetes en virtualenv, puede ser necesario
instalar paquetes en el sistema operativo.

El sistema requiere:
- PostgreSql 8 o superior
- Redis

Armado inicial del entorno
--------------------------

    $ git clone git@bitbucket.org:hgdeoro/ftsenderweb.git
    $ cd cd ftsenderweb/
    $ virtualenv -p python2.6 virtualenv
    $ . virtualenv/bin/activate
    $ pip install -r requirements.txt
    $ pip install -r requirements-dev.txt
    $ touch fts_web_settings_local.py
    $ pip install git+git://github.com/asterisk/starpy.git@408f2636d8eb879c787073dccf147cc5fe734cba

Editar fts_web_settings_local.py para que contenga:

	from fts_web_settings_local_dev import *

	SECRET_KEY = 'some-random-value'

	DATABASES = {
	    'default': {
	        'ENGINE': 'django.db.backends.postgresql_psycopg2',
	        'HOST': '127.0.0.1',
	        'PORT': 5432,
	        'NAME': 'NOMBRE_DE_LA_BASE_DE_DATOS',
	        'USER': 'USUARIO_DE_LA_BASE_DE_DATOS',
	        'PASSWORD': 'PASSWORD_DEL_USUARIO_DE_LA_BASE_DE_DATOS',
	        'CONN_MAX_AGE': 300,
	        'ATOMIC_REQUESTS': True,
	    }
	}

Crear usuario y BD de Postgresql:

    $ createuser -P USUARIO_DE_LA_BASE_DE_DATOS
    Enter password for new role:
    Enter it again:

    $ createdb -O USUARIO_DE_LA_BASE_DE_DATOS -E UNICODE NOMBRE_DE_LA_BASE_DE_DATOS

Sync de BD:

    $ ./manage.py syncdb
    $ ./manage.py migrate

El sistema puede lanzarse usando el servidor de desarrollo de Django:

    $ ./manage.py runserver

En otras dos consolas, se pueden lanzar los procesos de Celery:

    $ env DJANGO_SETTINGS_MODULE=fts_web.settings ./dev/celery_worker_finalizar_campana.sh
    $ env DJANGO_SETTINGS_MODULE=fts_web.settings ./dev/celery_worker_esperar_y_finalizar_campana.sh


Otras notas
===========

Dependencias
------------

Para instalar starpy:

    $ pip install git+git://github.com/asterisk/starpy.git@408f2636d8eb879c787073dccf147cc5fe734cba


Base de datos
-------------

Para facilitar la ejecucion de los tests, crear el lenguaje 'plpythonu' en
la BD 'template1', asi existe en las BD creadas por Django para ejecuar los tests.

    $ createlang plpythonu template1


Simulacion de envios
--------------------

Procedimiento para testing del daemon:

    $ USE_PG=1 FTS_SIMULADOR_DAEMON=1 ./run_uwsgi.sh

En otra consola:

    $ USE_PG=1 python manage.py crear_bd_contactos --cantidad=10000
    Iniciando INSERT de 10000 contactos...
    INSERT ok - BD: 160

    $ USE_PG=1 python manage.py crear_campana_basica --bd=160 --canales=30


Build / Deploy
--------------

Deploy a servidor de pruebas (VM):

    $ ./build.sh -i deploy/hosts-virtual-pruebas


Para testear conexion con Asterisk
----------------------------------

    $ FTS_RUN_ASTERISK_TEST=1 python manage.py test fts_tests.tests.tests_asterisk_ami_http.TestAsteriskHttpClient.test_ping_y_status


Para testear generacion de llamada con Asterisk
-----------------------------------------------

    $ FTS_RUN_ASTERISK_TEST=1 python manage.py test fts_tests.tests.tests_asterisk_ami_http.TestAsteriskHttpClient.login_y_originate_local_channel_async


Tunel SSH a Deployer/Git
------------------------

    $ ssh -vC -p 24922 -N -L 7777:127.0.0.1:80 deployer@190.210.28.37


Docker
======

Todo lo relacionado con Docker es de un nivel de madurez bajo.

Asterisk@Docker
---------------

Para lanzar Asterisk:

    $ ./deploy/docker-dev/run.sh

Para crear una campaña de prueba que tenga un archivo de audio valido:

    $ USE_PG=1 python manage.py crear_campana_basica --bd=28 --canales=5 --audio=test/wavs/8k16bitpcm.wav

Hay más informacion en deploy/README.txt
