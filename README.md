Entorno de desarrollo
=====================

El entorno utilizado para desarrollo es Ubuntu 14.04.

El sistema debe ser desarrollado usando Python 2.6 y virtualenv.

Para la instalación de algunos paquetes en virtualenv, puede ser necesario
instalar paquetes en el sistema operativo.

El sistema requiere que los siguientes sistemas estén funcionando:

 - PostgreSql 8 o superior, con 'plpythonu'
    - ANTES de crear la BD, ejecutar (con un usuario con permisos de administrador de Postgresql):
    - $ `createlang plpythonu template1`
 - Redis
 - Asterisk 11

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

    ##### [INICIO] #####

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

    # 'USERNAME' y 'PASSWORD': para acceder a la management console de Asterisk
    # 'HTTP_AMI_URL': URL para acceder a la management console
    # 'DIAL_URL': URL a usar para generar la llamada, debe contener '${NumberToCall}'
    ASTERISK = {
        'USERNAME': 'asterix-user',
        'PASSWORD': 'asterix-password',
        'HTTP_AMI_URL': 'http://127.0.0.1:7088',
        'DIAL_URL': "IAX2/10.1.5.1/${NumberToCall}",
    }

	# 'FTS_DIALPLAN_FILENAME': donde se genera el dialplan. Asterisk debe estar configurado
	#  para hacer un include de este archivo
	# **** RECORDAR: revisar permisos y que existan los directorios ****
    FTS_DIALPLAN_FILENAME = "/opt/data-tsunami/asterisk-11-d/etc/" + \
        "asterisk/fts/extensions.conf"

	# 'FTS_QUEUE_FILENAME': donde se genera la config de queues. Asterisk debe estar configurado
	#  para hacer un include de este archivo
	# **** RECORDAR: revisar permisos y que existan los directorios ****
    FTS_QUEUE_FILENAME = "/opt/data-tsunami/asterisk-11-d/etc/" + \
        "asterisk/fts/queues_fts.conf"

	# 'FTS_RELOAD_CMD': comando a ejecutar para realizar el reload de la configuracion de Asterisk
	# **** RECORDAR: revisar permisos, usuario, etc.
    FTS_RELOAD_CMD = ["/opt/data-tsunami/asterisk-11-d/sbin/asterisk",
        "-x", "reload"]

    ##### [FIN] #####

Crear usuario y BD de Postgresql:

    $ createuser -P --superuser USUARIO_DE_LA_BASE_DE_DATOS
    Enter password for new role:
    Enter it again:

    $ createdb -O USUARIO_DE_LA_BASE_DE_DATOS -E UNICODE NOMBRE_DE_LA_BASE_DE_DATOS

Sync de BD:

    $ ./manage.py syncdb
    $ ./manage.py migrate

Ejecucion del sistema por separado
----------------------------------

El sistema puede lanzarse usando el servidor de desarrollo de Django:

    $ ./manage.py runserver

Para tener toda la funcionalidad del sistema disponible, hace falta lanzar todos los demas
componentes:

    $ env DJANGO_SETTINGS_MODULE=fts_web.settings ./dev/celery_worker_finalizar_campana.sh
    $ env DJANGO_SETTINGS_MODULE=fts_web.settings ./dev/celery_worker_esperar_y_finalizar_campana.sh
    $ env DJANGO_SETTINGS_MODULE=fts_web.settings PYTHONPATH=. python ./fts_daemon/poll_daemon/main.py
    $ env DJANGO_SETTINGS_MODULE=fts_web.settings PYTHONPATH=. python ./fts_daemon/fastagi_daemon.py
    $ env DJANGO_SETTINGS_MODULE=fts_web.settings PYTHONPATH=. python ./fts_daemon/services/finalizador_vencidas_daemon.py

Para trabajar sobre la UI, si no se quieren ejecutar realmente las campañas, no hace falta
lanzar todos estos procesos, sólo 'runserver'.

Ejecucion del sistema desde uWSGI
---------------------------------

Existe un script que lanza la aplicación usando uWSGI, y junto a uWSGI, los daemons y workers de Celery.
La desventaja es que las clases no son recargadas automáticamente.

Para utilizar el sistema con uWSGI:

    $ ./run_uwsgi.sh


Settings
--------

Todos los settings posibles, con la correspondiente documentación, se encuentra
en 'fts_web.settings'.

Los settings definidos en 'fts_web_settings_local.py' *SOBREESCRIBEN* los valores de 'fts_web.settings'.
El archivo 'fts_web_settings_local.py' esta EXCLUIDO de git, para permitir que cada desarrollador configure allí
su entorno, sus IPs, etc.


Directorios & Paquetes
----------------------

 - fts_web: paquete con app Django
 - fts_daemon: paquete con daemon enviador (se comunica con Asterisk para generar llamadas)
 - fts_tests: paquete con tests pendientes de migrar

 - deploy: directorio con todo lo necesario para deploys automatizados
 - docs: fuentes de documentacion para generar con Sphinx (run_sphinx.sh)
 - dev: scripts y archivos y directorios temporales del ambiente de desarrollo
 - test: recursos estáticos requeridos para ejecución de tests automatizados

Scripts
-------

 - manage.py: manage de Django
 - build.sh: script de build automático, para hacer deploy de la app en servidores
 - run_uwsgi.sh: lanza uWSGI para desarrollo
 - run_sphinx.sh: genera documentación del sistema
 - run_coverage_daemon.sh: ejecuta tests & calcula coverage de funcionalidad del Daemon


# ----------------------------------------------------------------------------------------------------


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