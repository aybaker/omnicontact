#!/bin/bash

if [ `grep -c "appsms/DEMONIO-SMS"  /etc/rc.local` -eq 0 ];
then
echo "nohup python /home/ftsender/deploy/appsms/DEMONIO-SMS/supervisar.py &" >> /etc/rc.local
fi

if [ `grep -c "webservice/APLICACION_SOAP/"  /etc/rc.local` -eq 0 ];
then
echo "nohup python /home/ftsender/deploy/webservice/APLICACION_SOAP/supervisar.py &" >> /etc/rc.local
fi

if [ `grep -c "apidinstar/dinstar/"  /etc/rc.local` -eq 0 ];
then
echo "nohup /home/ftsender/deploy/apidinstar/dinstar/dwg.py start &" >> /etc/rc.local
fi
