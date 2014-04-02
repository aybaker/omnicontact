# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):

        # Changing field 'AgenteGrupoAtencion.numero_interno'
        db.alter_column(u'fts_web_agentegrupoatencion', 'numero_interno', self.gf('django.db.models.fields.PositiveIntegerField')(default=1))

        # Changing field 'GrupoAtencion.nombre'
        db.alter_column(u'fts_web_grupoatencion', 'nombre', self.gf('django.db.models.fields.CharField')(default=1, max_length=128))

        # Changing field 'GrupoAtencion.ring_strategy'
        db.alter_column(u'fts_web_grupoatencion', 'ring_strategy', self.gf('django.db.models.fields.PositiveIntegerField')())

        # Changing field 'GrupoAtencion.timeout'
        db.alter_column(u'fts_web_grupoatencion', 'timeout', self.gf('django.db.models.fields.PositiveIntegerField')(default=1))

        # Changing field 'Campana.reproduccion'
        db.alter_column(u'fts_web_campana', 'reproduccion', self.gf('django.db.models.fields.files.FileField')(default=1, max_length=100))

    def backwards(self, orm):

        # Changing field 'AgenteGrupoAtencion.numero_interno'
        db.alter_column(u'fts_web_agentegrupoatencion', 'numero_interno', self.gf('django.db.models.fields.PositiveIntegerField')(null=True))

        # Changing field 'GrupoAtencion.nombre'
        db.alter_column(u'fts_web_grupoatencion', 'nombre', self.gf('django.db.models.fields.CharField')(max_length=128, null=True))

        # Changing field 'GrupoAtencion.ring_strategy'
        db.alter_column(u'fts_web_grupoatencion', 'ring_strategy', self.gf('django.db.models.fields.PositiveIntegerField')(null=True))

        # Changing field 'GrupoAtencion.timeout'
        db.alter_column(u'fts_web_grupoatencion', 'timeout', self.gf('django.db.models.fields.PositiveIntegerField')(null=True))

        # Changing field 'Campana.reproduccion'
        db.alter_column(u'fts_web_campana', 'reproduccion', self.gf('django.db.models.fields.files.FileField')(max_length=100, null=True))

    models = {
        u'fts_web.agentegrupoatencion': {
            'Meta': {'object_name': 'AgenteGrupoAtencion'},
            'grupo_atencion': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "u'agentes'", 'to': u"orm['fts_web.GrupoAtencion']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'numero_interno': ('django.db.models.fields.PositiveIntegerField', [], {})
        },
        u'fts_web.campana': {
            'Meta': {'object_name': 'Campana'},
            'bd_contacto': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "u'campanas'", 'to': u"orm['fts_web.ListaContacto']"}),
            'estado': ('django.db.models.fields.PositiveIntegerField', [], {'default': '1'}),
            'fecha_fin': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'fecha_inicio': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'nombre': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'reproduccion': ('django.db.models.fields.files.FileField', [], {'max_length': '100'})
        },
        u'fts_web.contacto': {
            'Meta': {'object_name': 'Contacto'},
            'datos': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'lista_contacto': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "u'contactos'", 'to': u"orm['fts_web.ListaContacto']"}),
            'telefono': ('django.db.models.fields.CharField', [], {'max_length': '64'})
        },
        u'fts_web.grupoatencion': {
            'Meta': {'object_name': 'GrupoAtencion'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'nombre': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'ring_strategy': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            'timeout': ('django.db.models.fields.PositiveIntegerField', [], {})
        },
        u'fts_web.intentodecontacto': {
            'Meta': {'object_name': 'IntentoDeContacto'},
            'campana': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "u'intentos_de_contactos'", 'to': u"orm['fts_web.Campana']"}),
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