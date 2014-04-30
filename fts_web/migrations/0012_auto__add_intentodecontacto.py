# -*- coding: utf-8 -*-
# pylint: skip-file

from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'IntentoDeContacto'
        db.create_table(u'fts_web_intentodecontacto', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('contacto', self.gf('django.db.models.fields.related.ForeignKey')(related_name=u'+', to=orm['fts_web.Contacto'])),
            ('campana', self.gf('django.db.models.fields.related.ForeignKey')(related_name=u'+', to=orm['fts_web.Campana'])),
            ('fecha_intento', self.gf('django.db.models.fields.DateTimeField')(null=True, blank=True)),
            ('estado', self.gf('django.db.models.fields.PositiveIntegerField')(default=1)),
        ))
        db.send_create_signal(u'fts_web', ['IntentoDeContacto'])


    def backwards(self, orm):
        # Deleting model 'IntentoDeContacto'
        db.delete_table(u'fts_web_intentodecontacto')


    models = {
        u'fts_web.agentegrupoatencion': {
            'Meta': {'object_name': 'AgenteGrupoAtencion'},
            'grupo_atencion': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "u'agentes'", 'to': u"orm['fts_web.GrupoAtencion']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'numero_interno': ('django.db.models.fields.PositiveIntegerField', [], {'null': 'True', 'blank': 'True'})
        },
        u'fts_web.campana': {
            'Meta': {'object_name': 'Campana'},
            'bd_contacto': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "u'campanas'", 'to': u"orm['fts_web.ListaContacto']"}),
            'estado': ('django.db.models.fields.PositiveIntegerField', [], {'default': '1'}),
            'fecha_fin': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'fecha_inicio': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'nombre': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'reproduccion': ('django.db.models.fields.files.FileField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'})
        },
        u'fts_web.contacto': {
            'Meta': {'object_name': 'Contacto'},
            'datos': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'lista_contacto': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "u'contactos'", 'to': u"orm['fts_web.ListaContacto']"}),
            'telefono': ('django.db.models.fields.PositiveIntegerField', [], {})
        },
        u'fts_web.grupoatencion': {
            'Meta': {'object_name': 'GrupoAtencion'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'nombre': ('django.db.models.fields.CharField', [], {'max_length': '128', 'null': 'True', 'blank': 'True'}),
            'ring_strategy': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0', 'null': 'True', 'blank': 'True'}),
            'timeout': ('django.db.models.fields.PositiveIntegerField', [], {'null': 'True', 'blank': 'True'})
        },
        u'fts_web.intentodecontacto': {
            'Meta': {'object_name': 'IntentoDeContacto'},
            'campana': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "u'+'", 'to': u"orm['fts_web.Campana']"}),
            'contacto': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "u'+'", 'to': u"orm['fts_web.Contacto']"}),
            'estado': ('django.db.models.fields.PositiveIntegerField', [], {'default': '1'}),
            'fecha_intento': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'})
        },
        u'fts_web.listacontacto': {
            'Meta': {'object_name': 'ListaContacto'},
            'columnas': ('django.db.models.fields.CharField', [], {'max_length': '256', 'null': 'True', 'blank': 'True'}),
            'fecha_alta': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'nombre': ('django.db.models.fields.CharField', [], {'max_length': '128'})
        }
    }

    complete_apps = ['fts_web']