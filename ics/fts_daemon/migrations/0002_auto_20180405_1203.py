# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import os

from django.conf import settings
from django.db import models, migrations

"""
Esta migracion reemplaza a la migración South 0003_fk_constraints_testing
"""


NO_MIGRATIONS = []


def generate_runsqls():
    if 'FTS_DONT_USE_FK_CONSTRAINTS' in os.environ:
        print("Ignorando migracion: FTS_DONT_USE_FK_CONSTRAINTS")
        return NO_MIGRATIONS

    if not settings.FTS_TESTING_MODE:
        print("Ignorando migracion: no en FTS_TESTING_MODE")
        return NO_MIGRATIONS

    pg = 'django.db.backends.postgresql_psycopg2'
    if settings.DATABASES['default']['ENGINE'] != pg:
        print("Ignorando migracion: BD no es postgresql")
        return NO_MIGRATIONS

    return [
        migrations.RunSQL("""
        ALTER TABLE fts_daemon_eventodecontacto
            ADD CONSTRAINT contacto_id_fk
                FOREIGN KEY (contacto_id)
                    REFERENCES fts_web_contacto (id) MATCH FULL;
        """),
        migrations.RunSQL("""
        ALTER TABLE fts_daemon_eventodecontacto
            ADD CONSTRAINT campana_id_fk
                FOREIGN KEY (campana_id)
                    REFERENCES fts_web_campana (id) MATCH FULL;
        """),
    ]


class Migration(migrations.Migration):

    dependencies = [
        ('fts_daemon', '0001_initial'),
        ('fts_web', '0001_initial'),
    ]

    operations = generate_runsqls()
