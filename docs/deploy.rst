Deploy
======

IP de servidores:

 * ftsender-deployer: *192.168.99.224*
 * ftsender-produccion: *192.168.99.221*
 * ftsender-testing: *192.168.99.222*

Archivos de inventario:

 * ftsender-produccion: ~/hosts-virtual-freetech-produccion
 * ftsender-testing: ~/hosts-virtual-freetech-testing

Servidor de deploy
------------------

Nota: estos pasos ya fueron realizados en el servidor ``ftsender-deployer``.

Para crear el servidor de deploy se instalaron algunos paquetes, y se creó el usuario ``deployer``:

.. code::

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


Procedimiento de deploy en un nuevo servidor
--------------------------------------------

Estas son las instrucciones para realizar el deploy en un nuevo servidor (CentOS 6.5 de 32 bits).

Los comandos ejecutados en ``@new-server`` deben ejecutarse en el nuevo servidor, donde se quiere instalar el sistema.

Los comandos ejecutados en ``@ftsender-deployer`` deben ejecutarse en el servidor de deploy (192.168.99.224).


* Instalar paquetes requeridos:

.. code::

    root@new-server $ yum install libselinux-python

* Crear usuario ``ftsender``:

.. code::

    root@new-server $ adduser ftsender

* Configurar ``sudo`` para que el usuario ``ftsender`` pueda ejecutar cualquier comando sin que se le requiera el password:

.. code::

    root@new-server $ visudo
    # Cuando aparezca el editor, agregar la linea:

    ftsender ALL=(ALL)       NOPASSWD: ALL

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

     deployer@ftsender-deployer $ ssh ftsender@192.168.99.222

* Para realizar el deploy de la versión actual (en DESARROLLO, posiblemente inestable), ejecutar:

.. code::

    deployer@ftsender-deployer $ ./deploy.sh master ~/hosts-virtual-freetech-testing

* Para realizar el deploy de una versión específica, ejecutar:

.. code::

    deployer@ftsender-deployer $ ./deploy.sh <VERSION> ~/hosts-virtual-freetech-testing

En este caso, <VERSION> puede hacer referencia a un *tag* o *branch* de Git (ej: *v1.0.0*), o un commit específico (ej: *1eaf131fef84dc0c9fbea7bc095b6f8ec605fc56*).

Nota: actualmente para saber que versión deployar hace falta contactarse con los desarrolladores.

