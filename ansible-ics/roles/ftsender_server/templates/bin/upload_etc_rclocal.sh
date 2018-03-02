#!/bin/bash

if [ `grep -c "apidinstar/dinstar/"  /etc/rc.local` -eq 0 ];
then
echo "nohup /home/ftsender/deploy/apidinstar/dinstar/dwg.py start &" >> /etc/rc.local
fi
