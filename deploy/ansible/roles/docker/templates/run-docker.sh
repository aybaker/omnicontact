#!/bin/bash

COMPOSE_HTTP_TIMEOUT=200 /usr/local/bin/docker-compose up --build -d --force-recreate
ASTERISK_CONTAINER_ID=`docker ps -a |grep asterisk-omnileads |awk -F " " '{print $1}'`
KAMAILIO_CONTAINER_ID=`docker ps -a |grep rtpengine-kamailio |awk -F " " '{print $1}'`
asterisk_location=
kamailio_location=/opt/omnileads/kamailio

#docker exec -i $ASTERISK_CONTAINER_ID /bin/bash -c "chown -R omnileads. $asterisk_location &&  \
#                                                    service asterisk start && sleep 5 && asterisk -rx 'module load chan_sip.so' && asterisk -rx 'module reload'"
docker exec -i $KAMAILIO_CONTAINER_ID /bin/bash -c "echo 'y'| /opt/omnileads/kamailio/sbin/kamdbctl create"
