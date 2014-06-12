.. FTSender documentation master file, created by
   sphinx-quickstart on Wed Apr 30 10:52:05 2014.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Documentacion de FTSender
=========================

Arquitectura
------------

.. image:: arquitectura.png


Acceso al sistema
-----------------

El sistema puede ser accedido utilizando la URL http://ip-del-servidor:8088

Usuarios
--------

El sistema funciona bajo el usuario ``ftsender``. La aplicacion se encuentra en el directorio ``/home/ftsender/deploy``:

.. code::

    [ftsender@prueba-deploy-fts deploy]$ ls -lh ~/deploy/
    total 32K
    drwxr-xr-x. 6 ftsender root     4.0K May 21 22:17 app
    drwxr-xr-x. 2 ftsender root     4.0K May 21 22:17 bin
    drwxr-xr-x. 2 ftsender root     4.0K May 18 20:20 local
    drwxr-xr-x. 2 ftsender root     4.0K May 18 18:49 log
    drwxr-xr-x. 5 ftsender root     4.0K May 18 19:15 media_root
    drwxr-xr-x. 2 ftsender root     4.0K May 21 22:44 run
    drwxr-xr-x. 5 ftsender root     4.0K May 18 19:04 static_root
    drwxrwxr-x. 6 ftsender ftsender 4.0K May 18 19:36 virtualenv

En el directorio ``/home/ftsender/deploy/log`` se encuentran 2 archivos de log:

.. code::

    [ftsender@prueba-deploy-fts deploy]$ ls -lh ~/deploy/log/
    total 592K
    -rw-rw-r--. 1 ftsender ftsender  17K May 21 22:44 django.log
    -rw-r-----. 1 ftsender ftsender 565K May 21 22:44 uwsgi.log

En ``django.log`` se encuentran los logs de la aplicación.

Servicios
---------

El deploy del sistema incluye el setup de 2 servicios (Asterisk y FTSender):

.. code::

    [ftsender@prueba-deploy-fts deploy]$ ls -lh /etc/init.d/asterisk-11-ftsender /etc/init.d/ftsender-daemon 
    -rwxr-xr-x. 1 root root 1.7K May 21 22:17 /etc/init.d/asterisk-11-ftsender
    -rwxr-xr-x. 1 root root 1.8K May 18 19:20 /etc/init.d/ftsender-daemon

Para bajar el sistema FTSender (toda la aplicación: web y daemon), basta con ejecutar:

.. code::

    $ sudo service ftsender-daemon stop

Asterisk
--------

El sistema por default utiliza la instalación de Asterisk ubicada en ``/opt/asterisk-11``.
El script de deploy **modifica** los archivos allí encontrados para:

 * crear un usuario para el manager
 * activar la interfaz web
 * incluir los 2 archivos de configuración generados por el sistema (dialplan y queues).

Los archivos de configuración **generados por el sistema** son
guardados en el directorio ``/etc/ftsender/asterisk/``:

.. code::

    [ftsender@prueba-deploy-fts deploy]$ ls -lh /etc/ftsender/asterisk/
    total 4.0K
    -rw-r--r--. 1 ftsender ftsender 2.5K May 21 22:17 extensions.conf
    -rw-------. 1 ftsender ftsender    0 May 21 22:17 queues_fts.conf

Para acceder al CLI de Asterisk:

.. code::

    $ sudo -u asterisk /opt/asterisk-11/sbin/asterisk -rvvvv

Lo mismo para ejecutar comandos desde el shell:

.. code::

    $ sudo -u asterisk /opt/asterisk-11/sbin/asterisk -x 'core show calls'


Servidor de deploy
------------------

Nota: estos pasos ya fueron realizados en el servidor ``192.168.99.224``.

Para crear el servidor de deploy se instalaron algunos paquetes, y se creó el usuario ``deployer``:

.. code::

    root@deploy-server $ rpm -vih http://epel.mirror.mendoza-conicet.gob.ar/6/i386/epel-release-6-8.noarch.rpm
    root@deploy-server $ yum install python-virtualenv git
    root@deploy-server $ adduser deployer

Para armar el ambiente de deploy, hace falta ejecutar (con el usuario ``deployer``):

.. code::

    deployer@deploy-server $ cd ~
    deployer@deploy-server $ virtualenv virtualenv
    deployer@deploy-server $ . virtualenv/bin/activate
    deployer@deploy-server $ pip install ansible
    deployer@deploy-server $ git clone ssh://git@192.168.99.224/home/git/ftsenderweb.git
    deployer@deploy-server $ cd ftsenderweb/


Procedimiento de deploy en un nuevo servidor
--------------------------------------------

Estas son las instrucciones para realizar el deploy en un nuevo servidor. Se asume que inicialmente se tiene un servidor con CentOS 6.5 de 32 bits.

Los comandos ejecutados en ``new-server`` deben ejecutarse en el nuevo servidor, donde se quiere instalar el sistema.

Los comandos ejecutados en ``deploy-server`` deben ejecutarse en el servidor de deploy (192.168.99.224).


* Crear usuario ``ftsender``:

.. code::

    root@new-server $ adduser ftsender

* Configurar ``sudo`` para que el usuario ``ftsender`` pueda ejecutar cualquier comando sin que se le requiera el password:

.. code::

    root@new-server $ echo "ftsender ALL=(ALL)       NOPASSWD: ALL" >> /etc/sudoers.d/ftsender
    root@new-server $ echo "Defaults:ftsender        !requiretty"   >> /etc/sudoers.d/ftsender
    root@new-server $ chmod 0440 /etc/sudoers.d/ftsender

* Agregar el certificado de ``deployer`` a ``~/.ssh/authorized_keys``, para que pueda iniciar sesión sin requerir password.

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

     deployer@deploy-server $ ssh ftsender@192.168.99.222


Contents
--------

.. toctree::
   :maxdepth: 2
   :glob:

   fts_web_*
   fts_daemon_*


Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

