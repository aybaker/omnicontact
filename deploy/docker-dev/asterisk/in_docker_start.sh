#!/bin/bash

cp -fv /srv/asterisk/conf-runtime/*.conf /opt/asterisk-11/etc/asterisk/

# Creamos archivos vacios. EVITAMOS usar touch, usamos 'cp -p' para preservar permisos
[ ! -e /srv/asterisk/fts-conf/queues_fts.conf     ] && cp -p /srv/asterisk/fts-conf/empty /srv/asterisk/fts-conf/queues_fts.conf 
[ ! -e /srv/asterisk/fts-conf/extensions_fts.conf ] && cp -p /srv/asterisk/fts-conf/empty /srv/asterisk/fts-conf/extensions_fts.conf

/opt/asterisk-11/sbin/asterisk -f -q > /dev/null 2> /dev/null < /dev/null &

sleep 1

/opt/asterisk-11/sbin/asterisk -r -vvvvvvvvvvvv

kill %1

