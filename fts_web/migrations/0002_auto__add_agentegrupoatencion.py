# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'AgenteGrupoAtencion'
        db.create_table(u'fts_web_agentegrupoatencion', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('numero_interno', self.gf('django.db.models.fields.PositiveIntegerField')(null=True, blank=True)),
            ('grupo_atencion', self.gf('django.db.models.fields.related.ForeignKey')(related_name='agente_grupo_atencion', to=orm['fts_web.GrupoAtencion'])),
        ))
        db.send_create_signal(u'fts_web', ['AgenteGrupoAtencion'])


    def backwards(self, orm):
        # Deleting model 'AgenteGrupoAtencion'
        db.delete_table(u'fts_web_agentegrupoatencion')


    models = {
        u'fts_web.agentegrupoatencion': {
            'Meta': {'object_name': 'AgenteGrupoAtencion'},
            'grupo_atencion': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'agente_grupo_atencion'", 'to': u"orm['fts_web.GrupoAtencion']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'numero_interno': ('django.db.models.fields.PositiveIntegerField', [], {'null': 'True', 'blank': 'True'})
        },
        u'fts_web.grupoatencion': {
            'Meta': {'object_name': 'GrupoAtencion'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'nombre': ('django.db.models.fields.CharField', [], {'max_length': '128', 'null': 'True', 'blank': 'True'}),
            'ring_strategy': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            'timeout': ('django.db.models.fields.PositiveIntegerField', [], {'null': 'True', 'blank': 'True'})
        }
    }

    complete_apps = ['fts_web']