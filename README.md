
Dependencias
------------

Para instalar starpy:

    $ pip install git+git://github.com/asterisk/starpy.git@408f2636d8eb879c787073dccf147cc5fe734cba

Simulacion de envios
--------------------

Procedimiento para testing del daemon:

    $ USE_PG=1 FTS_SIMULADOR_DAEMON=1 ./run_uwsgi.sh

En otra consola:

    $ USE_PG=1 python manage.py crear_bd_contactos --cantidad=10000
    Iniciando INSERT de 10000 contactos...
    INSERT ok - BD: 160

    $ USE_PG=1 python manage.py crear_campana_basica --bd=160 --canales=30

