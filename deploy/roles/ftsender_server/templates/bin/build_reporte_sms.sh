#!/bin/bash

set -e

cp {{BUILD_DIR_REPORTE_SMS}}/reporte_sms.tar.gz /var/www/http/

tar -xzf /var/www/http/reporte_sms.tar.gz
