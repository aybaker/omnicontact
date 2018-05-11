# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.conf import settings
from django.db import models, migrations

"""
Esta migracion reemplaza a la migración South 0033_crea_tabla_cdr
"""


def generate_runsqls():
    pg = 'django.db.backends.postgresql_psycopg2'
    if settings.DATABASES['default']['ENGINE'] != pg:
        print("Ignorando migracion: BD no es postgresql")
        return []

    return [
        migrations.RunSQL("""
        CREATE TABLE fts_cdr (
            calldate timestamp without time zone NOT NULL,
            clid character varying(80) NOT NULL,
            src character varying(80) NOT NULL,
            dst character varying(80) NOT NULL,
            dcontext character varying(80) NOT NULL,
            channel character varying(80) NOT NULL,
            dstchannel character varying(80) NOT NULL,
            lastapp character varying(80) NOT NULL,
            lastdata character varying(80) NOT NULL,
            duration integer NOT NULL,
            billsec integer NOT NULL,
            disposition character varying(45) NOT NULL,
            amaflags integer NOT NULL,
            accountcode character varying(20) NOT NULL,
            uniqueid character varying(150) NOT NULL,
            userfield character varying(255) NOT NULL,
            peeraccount character varying(20) NOT NULL,
            linkedid character varying(150) NOT NULL,
            sequence integer NOT NULL)
        """)
    ]



class Migration(migrations.Migration):

    dependencies = [
        ('fts_web', '0002_auto_20180322_1624'),
    ]

    operations = generate_runsqls()
