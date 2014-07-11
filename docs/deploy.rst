.. highlight:: bash


Deploy
======


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





Acceso al servidor de deploy
----------------------------

Para acceder al servidor de deploy:

.. code::

    $ ssh deployer@192.168.99.224

Es recomendable agregar las claves públicas de quienes accederán en ``/home/deployer/.ssh/authorized_keys`` para evitar que solicite el password.






Procedimiento de deploy para servidor ya deployado
--------------------------------------------------

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


