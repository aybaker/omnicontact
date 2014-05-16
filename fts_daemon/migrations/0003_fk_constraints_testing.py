# -*- coding: utf-8 -*-
#@PydevCodeAnalysisIgnore
import os

from django.db import models
from south.db import db
from south.utils import datetime_utils as datetime
from south.v2 import SchemaMigration
from django.conf import settings


class Migration(SchemaMigration):

    def forwards(self, orm):

        if 'FTS_DONT_USE_FK_CONSTRAINTS' in os.environ:
            print("Ignorando migracion: FTS_DONT_USE_FK_CONSTRAINTS")
            return

        if not settings.FTS_TESTING_MODE:
            print("Ignorando migracion: no en FTS_TESTING_MODE")
            return

        pg = 'django.db.backends.postgresql_psycopg2'
        if settings.DATABASES['default']['ENGINE'] != pg:
            print("Ignorando migracion: BD no es postgresql")
            return

        sql = """
        ALTER TABLE fts_daemon_eventodecontacto
            ADD CONSTRAINT contacto_id_fk
                FOREIGN KEY (contacto_id)
                    REFERENCES fts_web_contacto (id) MATCH FULL;
        """
        db.execute(sql)

        sql = """
        ALTER TABLE fts_daemon_eventodecontacto
            ADD CONSTRAINT campana_id_fk
                FOREIGN KEY (campana_id)
                    REFERENCES fts_web_campana (id) MATCH FULL;
        """
        db.execute(sql)

    def backwards(self, orm):
        pass

    models = {
        u'fts_daemon.eventodecontacto': {
            'Meta': {'object_name': 'EventoDeContacto'},
            'campana_id': ('django.db.models.fields.IntegerField', [], {'db_index': 'True'}),
            'contacto_id': ('django.db.models.fields.IntegerField', [], {'db_index': 'True'}),
            'dato': ('django.db.models.fields.SmallIntegerField', [], {'db_index': 'True'}),
            'evento': ('django.db.models.fields.SmallIntegerField', [], {'db_index': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'timestamp': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'})
        }
    }

    complete_apps = ['fts_daemon']