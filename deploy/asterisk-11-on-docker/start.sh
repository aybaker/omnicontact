#!/bin/bash

/opt/asterisk-11/sbin/asterisk -f -q > /dev/null 2> /dev/null < /dev/null &

sleep 1

/opt/asterisk-11/sbin/asterisk -r -vvvvvvvvvvvv

kill %1

