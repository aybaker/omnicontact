# -*- coding: utf-8 -*-
# pylint: skip-file

from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'GrupoAtencion'
        db.create_table(u'fts_web_grupoatencion', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('nombre', self.gf('django.db.models.fields.CharField')(max_length=128, null=True, blank=True)),
            ('timeout', self.gf('django.db.models.fields.PositiveIntegerField')(null=True, blank=True)),
            ('ring_strategy', self.gf('django.db.models.fields.PositiveIntegerField')(default=0)),
        ))
        db.send_create_signal(u'fts_web', ['GrupoAtencion'])


    def backwards(self, orm):
        # Deleting model 'GrupoAtencion'
        db.delete_table(u'fts_web_grupoatencion')


    models = {
        u'fts_web.grupoatencion': {
            'Meta': {'object_name': 'GrupoAtencion'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'nombre': ('django.db.models.fields.CharField', [], {'max_length': '128', 'null': 'True', 'blank': 'True'}),
            'ring_strategy': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            'timeout': ('django.db.models.fields.PositiveIntegerField', [], {'null': 'True', 'blank': 'True'})
        }
    }

    complete_apps = ['fts_web']