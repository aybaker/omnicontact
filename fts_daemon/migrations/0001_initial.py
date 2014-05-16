# -*- coding: utf-8 -*-
#@PydevCodeAnalysisIgnore
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'EventoDeContacto'
        db.create_table(u'fts_daemon_eventodecontacto', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('campana_id', self.gf('django.db.models.fields.IntegerField')(db_index=True)),
            ('contacto_id', self.gf('django.db.models.fields.IntegerField')(db_index=True)),
            ('timestamp', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('evento', self.gf('django.db.models.fields.SmallIntegerField')(db_index=True)),
            ('dato', self.gf('django.db.models.fields.SmallIntegerField')(null=True)),
        ))
        db.send_create_signal(u'fts_daemon', ['EventoDeContacto'])


    def backwards(self, orm):
        # Deleting model 'EventoDeContacto'
        db.delete_table(u'fts_daemon_eventodecontacto')


    models = {
        u'fts_daemon.eventodecontacto': {
            'Meta': {'object_name': 'EventoDeContacto'},
            'campana_id': ('django.db.models.fields.IntegerField', [], {'db_index': 'True'}),
            'contacto_id': ('django.db.models.fields.IntegerField', [], {'db_index': 'True'}),
            'dato': ('django.db.models.fields.SmallIntegerField', [], {'null': 'True'}),
            'evento': ('django.db.models.fields.SmallIntegerField', [], {'db_index': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'timestamp': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'})
        }
    }

    complete_apps = ['fts_daemon']