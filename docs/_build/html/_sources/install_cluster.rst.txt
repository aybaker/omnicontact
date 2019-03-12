Horizontal Cluster Installation
===============================

Existen dos formas de dividir los componentes de OML.


En 5 hosts:
omniapp: contiene los servicios uwsgi, php-fpm, nginx, por lo tanto es aca donde estan el repositorio con el código de la aplicación
kamailio: con kamailio, rtpengine
asterisk: contiene asterisk y todos sus servicios
database: contiene la base de datos postgresql
dialer: contiene la aplicación wombat dialer con su respectiva base de datos
