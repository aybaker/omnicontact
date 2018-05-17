# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import os

from django.conf import settings
from django.db import models, migrations

"""
Esta migracion reemplaza a la migración South 0013_crea_update_agreg_plpython
"""


def generate_runsqls():
    """
    Aplica migracion. SOLO la aplica cuando la variable FTS_TESTING_MODE
    esta seteada en True.

    Con respecto al DEPLOY en PRODUCCION (y otros ambientes), esta
    bien que no se aplique esta migracion, ya que el script de deploy
    ejecuta directamente los archivos .SQL
    """
    if not settings.FTS_TESTING_MODE:
        print("Ignorando migracion: no en FTS_TESTING_MODE")
        return []

    pg = 'django.db.backends.postgresql_psycopg2'
    if settings.DATABASES['default']['ENGINE'] != pg:
        print("Ignorando migracion: BD no es postgresql")
        return

    tmp_dir = os.path.abspath(__file__)  # (this file)
    tmp_dir = os.path.dirname(tmp_dir)  # migrations
    tmp_dir = os.path.split(tmp_dir)[0]  # fts_web

    run_sqls = []

    for sql_file_path in (
            "sql/plpython/update_agregacion_edc_py_v1.sql",
            "sql/plpython/recalculate_agregacion_edc_py_v1.sql"
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
        ('fts_web', '0001_initial'),
    ]

    operations = generate_runsqls()
