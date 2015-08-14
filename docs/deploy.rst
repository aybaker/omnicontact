.. highlight:: bash


Deploy
======


.. caution::

    A fines de octubre/2014 se creo un nuevo deployer, repositorio git y servidor de doc. Estos
    cambios todavia no estan reflejados en la documentación.

.. caution::

    Al deployar en CentOS 6.7 x64, SELinux no permite que NGINX inicie en el puerto que usamos.
    La solución es configurar SELinux para que permita usar el puerto alternativo, y como
    workaround, se puede desactivar SELinux (esto NO es recomendado, sobre todo en ambientes productivos).

.. note::

    Los scripts de deploy estan probados extensivamente en arquitectura i386.

    Para usarlos en amd64, al menos hará falta definir `BUILD_ASTERISK_CFLAGS` en el archivo
    de inventario (en los casos en que el script de deploy debe compilar e instalar Asterisk),
    por ejemplo:

        `BUILD_ASTERISK_CFLAGS=''`


IP de servidores
----------------

 * ftsender-deployer: *192.168.99.224*
 * ftsender-produccion: *192.168.99.221*
 * ftsender-testing: *192.168.99.222*

Para agilizar la presentación de cada Sprint, los desarrolladores realizarán un deploy al servidor de testing. 



Archivos de inventario
----------------------

Estos archivos de inventarios se encuentran el el servidor de deploy:

 * ftsender-produccion: ~/hosts-virtual-freetech-produccion
 * ftsender-testing: ~/hosts-virtual-freetech-testing



Customizacion de settings
-------------------------

Para customizar el sistema, se pueden cargar seteos en el archivo
**/home/ftsender/deploy/local/fts_web_settings_local_customizations.py**. Este archivo
debe tener la sintaxis de un módulo Python. Si el sistema encuentra algún problema
al leerlo, los seteos allí configurados serán ignorados completamente.


Para chequear que no existen errores de sintaxis, puede ejecutar dicho archivo con python:

.. code::

    $ python /home/ftsender/deploy/local/fts_web_settings_local_customizations.py

Si el archivo tiene algun problema, éste será reportado. Si no se genera ninguna salida por pantalla,
esto implica que el archivo es válido.


Ejemplos:

.. code-block:: python

    # Para permitir 5 originate por segundo
    FTS_DAEMON_ORIGINATES_PER_SECOND = 5.0

    # Para permitir 1 originate cada 5 segundos
    FTS_DAEMON_ORIGINATES_PER_SECOND = 1.0 / 5.0

    # Para generar el archivo de QUEUEs de Asterisk en una ubicacion diferente a la por defalut
    FTS_QUEUE_FILENAME = '/opt/asterisk/etc/queues.conf'

    # Para permitir numeros telefonicos de entre 5 y 30 cifras
    FTS_NRO_TELEFONO_LARGO_MIN = 5
    FTS_NRO_TELEFONO_LARGO_MAX = 30


Acceso al servidor de deploy
----------------------------

Para acceder al servidor de deploy:

.. code::

    $ ssh deployer@192.168.99.224

Es recomendable agregar las claves públicas de quienes accederán en ``/home/deployer/.ssh/authorized_keys`` para evitar que solicite el password.


Creacion de usuarios para acceder al sistema
--------------------------------------------

En el Sprint 7 se implemento la autenticación de ususarios.

Para crear usuarios, es necesario loguearse en el servidor con el usuario `ftsender`
y ejecutar `/home/ftsender/deploy/bin/manage.sh create_ftsender_user`:

.. code::

    $ host> ssh ftsender@server-or-ip
    $ server> /home/ftsender/deploy/bin/manage.sh create_ftsender_user




Procedimiento de deploy
-----------------------

Para realizar el deploy del sistema debe utilizar el usuario **deployer**, y ejecutar:

.. code::

    deployer@ftsender-deployer $ ./deploy.sh <BRANCH> <INVENTARIO>

**<BRANCH>** hace referencia al branch de Git a deployar (el nombre del branch para cada Sprint está documentado
en los release notes). Los branches poseen la forma **sprintNN** o **sprintNN-fixes** (donde NN es el número de sprint).

**<INVENTARIO>** hace referencia al archivo de inventario, donde está identificado un host
donde se realizará el deploy, con todas sus customizaciones. Debe especificarse el PATH ABSOLUTO
a dicho archivo, por ejemplo: ~/hosts-virtual-freetech-produccion o ~/hosts-virtual-freetech-testing.

.. note::

    Si es la primera vez que se va a realizar el deploy en el servidor (o sea, es un servidor nuevo),
    recuerde realizar el setup inicial, siguiendo las instrucciones de `Setup inicial de nuevo servidor`_.

    Además, es recomendable reiniciar el servidor luego de realizar el primer deploy, ya que la primera vez
    se crean y activan varios servicios.



Deploy de versión más nueva del software (en desarrollo)
........................................................

Para realizar el deploy de la versión actual (en DESARROLLO, posiblemente inestable), ejecutar:

.. code::

    deployer@ftsender-deployer $ ./deploy.sh master ~/hosts-virtual-freetech-testing

.. warning::

    La versión actual en desarrollo puede contener bugs, funcionalidad implementada
    parcialmente, etc., por lo que en general NO es recomendable deployar 'master'.




Setup inicial de nuevo servidor
-------------------------------

Estas son las instrucciones para realizar el setup inicial de un nuevo servidor. Este procedimiento
necesita ser ejecutado **una vez**.

.. note::

    Los comandos ejecutados en ``@new-server`` deben ejecutarse en el nuevo servidor, donde se quiere instalar el sistema.

    Los comandos ejecutados en ``@ftsender-deployer`` deben ejecutarse en el servidor de deploy (192.168.99.224).


Chequear versión: CentOS 6.5
............................

El deploy automatizado fue probado en CentOS 6.5. Para asegurar el correcto funcionamiento, verificar la versión del sistema operativo:


.. code::

    root@new-server $ cat /etc/centos-release 
    CentOS release 6.5 (Final)


Desactivar SELinux
..................

Desactivar SELinux hace al servidor mucho más vulnerable, pero puede ser necesario para
utilizar el sistema con CentOS posteriores a 6.5, ya que las nuevas versiones de CentOS
pueden traer controles activados que en la versión 6.5 no existían.

Para desactivarlo, hace falta editar el archivo ``/etc/selinux/config``, setear
el valor ``SELINUX=permissive``, y reiniciar el servidor para asegurarnos que
haya tomado la configuración.

.. code::

    root@new-server $ vim /etc/selinux/config

Para verificar que SELinux esta desactivado, se puede utilizar ``getenforce``. Si dicho
comando muestra por pantalla ``Permissive``, es porque SELinux está desactivado:

.. code::

    root@new-server $ getenforce
    Permissive


Instalar paquetes requeridos
............................

.. code::

    root@new-server $ yum install libselinux-python

Crear usuario ``ftsender``
..........................

.. code::

    root@new-server $ adduser ftsender

Configurar sudo
...............

Configurar ``sudo`` para que el usuario ``ftsender`` pueda ejecutar cualquier comando sin que se le requiera el password:

.. code::

    root@new-server $ visudo
    # Cuando aparezca el editor, agregar la linea:

    ftsender ALL=(ALL)       NOPASSWD: ALL

Configurar acceso ssh
.....................

Agregar el certificado de ``deployer`` a ``~/.ssh/authorized_keys``, para que pueda iniciar sesión sin requerir password.

.. code::

    ftsender@new-sever $ mkdir .ssh
    ftsender@new-sever $ chmod 0700 .ssh
    ftsender@new-sever $ vi ~/.ssh/authorized_keys
    ## AGREGAR el certificado publico de deployer
    ftsender@new-sever $ chmod 0600 ~/.ssh/authorized_keys
    ftsender@new-sever $ restorecon -R ~/.ssh

El certificado del usuario ``deployer`` del servidor ``192.168.99.224`` es:

.. code::

    ssh-rsa AAAAB3NzaC1yc2EAAAABIwAAAQEAwGz4+GZ7R+5JyPdVQmYLG48kGXgjm/Wb/ZFgaLleV/qmJj6eeK8jnkHImERBj5fgLX9Xq3Fp6syxNJMHPn3dZSNTCRCETGcYhCS/9btHCt6V0IxWhPboCKWjz3PDV95E+uki3QesT5lvDrHErkCdsIgypgoNNs/Z0tF6u5ScsmWiaoRKeFd85Okg2rD3jznLGWvFSKbIHUDjjgdqZ34DDxYzHmYD0UNl0rDm0i5RrtuILQNaTnKCK+kbJO6PpCy5MHy8GO5lVF/UHOv8cfvbX5xp5PvPykyhJIXJ/W1/KZBfMR194cMrClH8NPEH8cNsl4CR78xzulqaU5wZLiCplQ== deployer@ftsender-deployer.example.com

Para verificar que el usuario ``deployer`` puede acceder al nuevo servidor, ejecutar:

.. code::

     deployer@ftsender-deployer $ ssh ftsender@192.168.99.222





Servidor de deploy
------------------

.. note::

    Nota: estos pasos ya fueron realizados en el servidor ``ftsender-deployer``.

Para crear el servidor de deploy se instalaron algunos paquetes, y se creó el usuario ``deployer``:

.. code::

    root@ftsender-deployer $ yum groupinstall "Development tools"
    root@ftsender-deployer $ rpm -vih http://epel.mirror.mendoza-conicet.gob.ar/6/i386/epel-release-6-8.noarch.rpm
    root@ftsender-deployer $ yum install python-virtualenv git
    root@ftsender-deployer $ adduser deployer

Para armar el ambiente de deploy, hace falta ejecutar (con el usuario ``deployer``):

.. code::

    deployer@ftsender-deployer $ cd ~
    deployer@ftsender-deployer $ virtualenv virtualenv
    deployer@ftsender-deployer $ . virtualenv/bin/activate
    deployer@ftsender-deployer $ pip install ansible
    deployer@ftsender-deployer $ git clone ssh://git@192.168.99.224/home/git/ftsenderweb.git
    deployer@ftsender-deployer $ cd ftsenderweb/


