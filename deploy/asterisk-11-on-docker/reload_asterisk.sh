#!/bin/bash

docker run \
	-v /opt/data-tsunami/fts/asterisk/conf:/opt/data-tsunami/fts/asterisk/conf \
	-v /opt/data-tsunami/fts/asterisk/run:/opt/asterisk-11/var/run/asterisk \
	-ti hgdeoro/fts-asterisk-dev \
	/opt/asterisk-11/sbin/asterisk -x reload
