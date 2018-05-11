#!/bin/bash

cp -fv /srv/asterisk/conf-runtime/*.conf /opt/asterisk-11/etc/asterisk/

mv -fv /opt/asterisk-11/etc/asterisk/cdr_pgsql_integration_testing.conf /opt/asterisk-11/etc/asterisk/cdr_pgsql.conf

# Creamos archivos vacios. EVITAMOS usar touch, usamos 'cp -p' para preservar permisos
[ ! -e /srv/asterisk/fts-conf/queues_fts.conf     ] && cp -p /srv/asterisk/fts-conf/empty /srv/asterisk/fts-conf/queues_fts.conf 
[ ! -e /srv/asterisk/fts-conf/extensions_fts.conf ] && cp -p /srv/asterisk/fts-conf/empty /srv/asterisk/fts-conf/extensions_fts.conf

/opt/asterisk-11/sbin/asterisk -f -n -v 2>&1
