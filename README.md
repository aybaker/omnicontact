
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


Asterisk@Docker
---------------

Para lanzar Asterisk:

    $ ./deploy/docker-dev/run.sh

Para crear una campaña de prueba que tenga un archivo de audio valido:

    $ USE_PG=1 python manage.py crear_campana_basica --bd=28 --canales=5 --audio=test/wavs/8k16bitpcm.wav

Hay más informacion en deploy/README.txt


Para testear conexion con Asterisk
----------------------------------

    $ FTS_RUN_ASTERISK_TEST=1 python manage.py test fts_tests.tests.tests_asterisk_ami_http.TestAsteriskHttpClient.test_ping_y_status


Para testear generacion de llamada con Asterisk
-----------------------------------------------

    $ FTS_RUN_ASTERISK_TEST=1 python manage.py test fts_tests.tests.tests_asterisk_ami_http.TestAsteriskHttpClient.login_y_originate_local_channel_async

