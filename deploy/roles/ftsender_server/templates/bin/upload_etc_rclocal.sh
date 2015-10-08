#!/bin/bash

if [ `grep -c "appsms/DEMONIO-SMS"  /etc/rc.local` -eq 0 ];
then
echo "nohup python /home/ftsender/deploy/appsms/DEMONIO-SMS/supervisar.py &" >> /etc/rc.local
fi
