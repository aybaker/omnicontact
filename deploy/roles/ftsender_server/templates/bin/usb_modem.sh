#!/bin/bash

if [ ! test -f /var/spool/cron/root ];
then
touch /var/spool/cron/root
echo "*/4 * * * * /usr/sbin/3g_switch" >> /var/spool/cron/root
chmod 777 /var/spool/cron/root
fi

if [ ! test -f /etc/rc.modules ];
then
echo "modprobe option" /etc/rc.modules
chmod 777 /etc/rc.modules
fi
