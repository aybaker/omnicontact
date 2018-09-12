#!/bin/bash

COMPOSE_HTTP_TIMEOUT=200 /usr/local/bin/docker-compose up --build -d
ASTERISK_CONTAINER_ID=`docker ps -a |grep asterisk-omnileads |awk -F " " '{print $1}'`
KAMAILIO_CONTAINER_ID=`docker ps -a |grep rtpengine-kamailio |awk -F " " '{print $1}'`
asterisk_location={{ asterisk_location }}
kamailio_location={{ kamailio_location }}

docker exec -i $ASTERISK_CONTAINER_ID /bin/bash -c "chown -R omnileads. $asterisk_location &&  \
                                                    service asterisk start && sleep 5 && asterisk -rx 'module load chan_sip.so' && asterisk -rx 'module reload'"
docker exec -i $KAMAILIO_CONTAINER_ID /bin/bash -c "chown -R omnileads. $kamailio_location"

#docker cp kamailio:{{ kamailio_location }}/etc/certs/cert.pem {{ install_prefix }}nginx_certs/
#docker cp kamailio:{{ kamailio_location }}/etc/certs/key.pem {{ install_prefix }}nginx_certs/
#docker cp kamailio:/tmp/voip.cert {{ install_prefix }}static/ominicontacto/voip.cert
#chown -R omnileads. {{ install_prefix }}nginx_certs
