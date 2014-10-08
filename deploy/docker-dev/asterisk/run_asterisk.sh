#!/bin/bash

if [ ! -e /opt/data-tsunami/fts/asterisk/conf/.placeholder ] ; then
	sudo mkdir -p /opt/data-tsunami/fts/asterisk/conf
	sudo chown $UID /opt/data-tsunami/fts/asterisk/conf
	sudo chmod 0755 /opt/data-tsunami/fts/asterisk/conf
        touch /opt/data-tsunami/fts/asterisk/conf/.placeholder
fi

docker run \
	-p 5060:5060/udp -p 7088:7088 \
	-v /opt/data-tsunami/fts/asterisk/conf:/opt/data-tsunami/fts/asterisk/conf \
	-v /opt/data-tsunami/fts/asterisk/run:/opt/asterisk-11/var/run/asterisk \
	-ti hgdeoro/fts-asterisk-dev

