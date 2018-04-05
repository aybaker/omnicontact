# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.conf import settings
from django.db import models, migrations

"""
Esta migracion reemplaza a la migración South 0052_add_table_consultas_sms
"""


def generate_runsqls():
    pg = 'django.db.backends.postgresql_psycopg2'
    if settings.DATABASES['default']['ENGINE'] != pg:
        print("Ignorando migracion: BD no es postgresql")
        return []

    sql_statements = []

    # Crea tabla consultas_sms
    sql = """
        CREATE TABLE consultas_sms (
            fecha timestamp(0) WITHOUT time zone NOT NULL DEFAULT LOCALTIMESTAMP(0),
            token varchar(50) NOT NULL,
            metadatos varchar(200) NOT NULL,
            estado varchar(255) NOT NULL,
            userfield varchar(20) NOT NULL,
            password varchar(20) NOT NULL,
            datos1 text NOT NULL,
            datos2 text NOT NULL,
            datos3 text NOT NULL,
            datos4 text NOT NULL,
            datos5 text NOT NULL,
            datos6 text NOT NULL,
            datos7 text NOT NULL,
            datos8 text NOT NULL,
            datos9 text NOT NULL,
            datos10 text NOT NULL,
            PRIMARY KEY (token)
        )
    """
    sql_statements.append(sql)

    # Crea indices para la tabla consultas_sms
    sql = """
        CREATE INDEX consultas_sms_token ON consultas_sms(token)
    """
    sql_statements.append(sql)

    sql = """
        CREATE INDEX consultas_sms_fecha ON consultas_sms(fecha)
    """
    sql_statements.append(sql)

    return list(map(migrations.RunSQL, sql_statements))


class Migration(migrations.Migration):

    dependencies = [
        ('fts_web', '0005_auto_20180405_1135'),
    ]

    operations = generate_runsqls()
