# -*- coding: utf-8 -*-
# pylint: skip-file

from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding field 'AgenteGrupoAtencion.active'
        db.add_column(u'fts_web_agentegrupoatencion', 'active',
                      self.gf('django.db.models.fields.BooleanField')(default=True),
                      keep_default=False)

        # Adding field 'GrupoAtencion.active'
        db.add_column(u'fts_web_grupoatencion', 'active',
                      self.gf('django.db.models.fields.BooleanField')(default=True),
                      keep_default=False)


    def backwards(self, orm):
        # Deleting field 'AgenteGrupoAtencion.active'
        db.delete_column(u'fts_web_agentegrupoatencion', 'active')

        # Deleting field 'GrupoAtencion.active'
        db.delete_column(u'fts_web_grupoatencion', 'active')


    models = {
        u'fts_web.agentegrupoatencion': {
            'Meta': {'object_name': 'AgenteGrupoAtencion'},
            'active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'grupo_atencion': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'agente_grupo_atencion'", 'to': u"orm['fts_web.GrupoAtencion']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'numero_interno': ('django.db.models.fields.PositiveIntegerField', [], {'null': 'True', 'blank': 'True'})
        },
        u'fts_web.grupoatencion': {
            'Meta': {'object_name': 'GrupoAtencion'},
            'active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'nombre': ('django.db.models.fields.CharField', [], {'max_length': '128', 'null': 'True', 'blank': 'True'}),
            'ring_strategy': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0', 'null': 'True', 'blank': 'True'}),
            'timeout': ('django.db.models.fields.PositiveIntegerField', [], {'null': 'True', 'blank': 'True'})
        }
    }

    complete_apps = ['fts_web']