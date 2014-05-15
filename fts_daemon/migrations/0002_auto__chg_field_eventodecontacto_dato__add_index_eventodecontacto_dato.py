# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):

        # Changing field 'EventoDeContacto.dato'
        db.alter_column(u'fts_daemon_eventodecontacto', 'dato', self.gf('django.db.models.fields.SmallIntegerField')(default=None))
        # Adding index on 'EventoDeContacto', fields ['dato']
        db.create_index(u'fts_daemon_eventodecontacto', ['dato'])


    def backwards(self, orm):
        # Removing index on 'EventoDeContacto', fields ['dato']
        db.delete_index(u'fts_daemon_eventodecontacto', ['dato'])


        # Changing field 'EventoDeContacto.dato'
        db.alter_column(u'fts_daemon_eventodecontacto', 'dato', self.gf('django.db.models.fields.SmallIntegerField')(null=True))

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