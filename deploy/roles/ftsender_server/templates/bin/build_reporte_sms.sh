#!/bin/bash

set -e

cp /home/ftsender/deploy/appsms/reporte_sms.tar.gz /var/www/http/

tar -xzf /var/www/http/reporte_sms.tar.gz
