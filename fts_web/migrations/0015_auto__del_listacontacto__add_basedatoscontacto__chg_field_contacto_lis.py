# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Deleting model 'ListaContacto'
        db.delete_table(u'fts_web_listacontacto')

        # Adding model 'BaseDatosContacto'
        db.create_table(u'fts_web_basedatoscontacto', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('nombre', self.gf('django.db.models.fields.CharField')(max_length=128)),
            ('fecha_alta', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('columnas', self.gf('django.db.models.fields.CharField')(max_length=256, null=True, blank=True)),
        ))
        db.send_create_signal(u'fts_web', ['BaseDatosContacto'])


        # Changing field 'Contacto.lista_contacto'
        db.alter_column(u'fts_web_contacto', 'lista_contacto_id', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['fts_web.BaseDatosContacto']))

        # Changing field 'Campana.bd_contacto'
        db.alter_column(u'fts_web_campana', 'bd_contacto_id', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['fts_web.BaseDatosContacto']))

    def backwards(self, orm):
        # Adding model 'ListaContacto'
        db.create_table(u'fts_web_listacontacto', (
            ('nombre', self.gf('django.db.models.fields.CharField')(max_length=128)),
            ('columnas', self.gf('django.db.models.fields.CharField')(max_length=256, null=True, blank=True)),
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('fecha_alta', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
        ))
        db.send_create_signal(u'fts_web', ['ListaContacto'])

        # Deleting model 'BaseDatosContacto'
        db.delete_table(u'fts_web_basedatoscontacto')


        # Changing field 'Contacto.lista_contacto'
        db.alter_column(u'fts_web_contacto', 'lista_contacto_id', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['fts_web.ListaContacto']))

        # Changing field 'Campana.bd_contacto'
        db.alter_column(u'fts_web_campana', 'bd_contacto_id', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['fts_web.ListaContacto']))

    models = {
        u'fts_web.agentegrupoatencion': {
            'Meta': {'object_name': 'AgenteGrupoAtencion'},
            'grupo_atencion': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "u'agentes'", 'to': u"orm['fts_web.GrupoAtencion']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'numero_interno': ('django.db.models.fields.PositiveIntegerField', [], {})
        },
        u'fts_web.basedatoscontacto': {
            'Meta': {'object_name': 'BaseDatosContacto'},
            'columnas': ('django.db.models.fields.CharField', [], {'max_length': '256', 'null': 'True', 'blank': 'True'}),
            'fecha_alta': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'nombre': ('django.db.models.fields.CharField', [], {'max_length': '128'})
        },
        u'fts_web.campana': {
            'Meta': {'object_name': 'Campana'},
            'bd_contacto': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "u'campanas'", 'to': u"orm['fts_web.BaseDatosContacto']"}),
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
            'lista_contacto': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "u'contactos'", 'to': u"orm['fts_web.BaseDatosContacto']"}),
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
        }
    }

    complete_apps = ['fts_web']