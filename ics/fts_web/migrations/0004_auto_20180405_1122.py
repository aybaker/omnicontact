# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import os

from django.conf import settings
from django.db import models, migrations

"""
Esta migracion reemplaza a la migración South 0049_crea_update_timestamp_plpgsql
"""


def generate_runsqls():
    pg = 'django.db.backends.postgresql_psycopg2'
    if settings.DATABASES['default']['ENGINE'] != pg:
        print("Ignorando migracion: BD no es postgresql")
        return

    tmp_dir = os.path.abspath(__file__)  # (this file)
    tmp_dir = os.path.dirname(tmp_dir)  # migrations
    tmp_dir = os.path.split(tmp_dir)[0]  # fts_web

    run_sqls = []

    for sql_file_path in (
            "sql/plpgsql/update_timestamp.sql",
    ):
        tmp = os.path.join(tmp_dir, sql_file_path)

        assert os.path.exists(tmp)

        print("Creando funcion desde {0}".format(tmp))
        filename = tmp
        sql = open(filename, "r").read()
        run_sqls.append(migrations.RunSQL(sql))

    return run_sqls


class Migration(migrations.Migration):

    dependencies = [
        ('fts_web', '0003_auto_20180322_1641'),
    ]

    operations = generate_runsqls()
