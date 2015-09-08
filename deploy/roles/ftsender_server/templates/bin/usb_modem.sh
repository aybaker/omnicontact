#!/bin/bash

`test -f /var/spool/cron/root`
var=`echo "$?"`

if [ $var -eq 1 ];
then
echo "*/4 * * * * /usr/sbin/3g_switch" >> /var/spool/cron/root
fi

`test -f /etc/rc.modules`
var=`echo "$?"`

if [ $var -eq 1 ];
then
touch /etc/rc.modules
echo "modprobe option" /etc/rc.modules
chmod 777 /etc/rc.modules
fi
