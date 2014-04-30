# -*- coding: utf-8 -*-
# pylint: skip-file

from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding field 'ListaContacto.fecha_alta'
        db.add_column(u'fts_web_listacontacto', 'fecha_alta',
                      self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, default=datetime.datetime(2014, 3, 28, 0, 0), blank=True),
                      keep_default=False)

        # Adding field 'ListaContacto.columnas'
        db.add_column(u'fts_web_listacontacto', 'columnas',
                      self.gf('django.db.models.fields.CharField')(max_length=256, null=True, blank=True),
                      keep_default=False)


    def backwards(self, orm):
        # Deleting field 'ListaContacto.fecha_alta'
        db.delete_column(u'fts_web_listacontacto', 'fecha_alta')

        # Deleting field 'ListaContacto.columnas'
        db.delete_column(u'fts_web_listacontacto', 'columnas')


    models = {
        u'fts_web.agentegrupoatencion': {
            'Meta': {'object_name': 'AgenteGrupoAtencion'},
            'active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'grupo_atencion': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "u'agente_grupo_atencion'", 'to': u"orm['fts_web.GrupoAtencion']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'numero_interno': ('django.db.models.fields.PositiveIntegerField', [], {'null': 'True', 'blank': 'True'})
        },
        u'fts_web.campana': {
            'Meta': {'object_name': 'Campana'},
            'bd_contacto': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "u'campanas'", 'to': u"orm['fts_web.ListaContacto']"}),
            'estado': ('django.db.models.fields.PositiveIntegerField', [], {'default': '1'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'nombre': ('django.db.models.fields.CharField', [], {'max_length': '128'})
        },
        u'fts_web.contacto': {
            'Meta': {'object_name': 'Contacto'},
            'active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'datos': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'lista_contacto': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "u'contactos'", 'to': u"orm['fts_web.ListaContacto']"}),
            'telefono': ('django.db.models.fields.PositiveIntegerField', [], {})
        },
        u'fts_web.grupoatencion': {
            'Meta': {'object_name': 'GrupoAtencion'},
            'active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'nombre': ('django.db.models.fields.CharField', [], {'max_length': '128', 'null': 'True', 'blank': 'True'}),
            'ring_strategy': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0', 'null': 'True', 'blank': 'True'}),
            'timeout': ('django.db.models.fields.PositiveIntegerField', [], {'null': 'True', 'blank': 'True'})
        },
        u'fts_web.listacontacto': {
            'Meta': {'object_name': 'ListaContacto'},
            'active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'columnas': ('django.db.models.fields.CharField', [], {'max_length': '256', 'null': 'True', 'blank': 'True'}),
            'fecha_alta': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'nombre': ('django.db.models.fields.CharField', [], {'max_length': '128'})
        }
    }

    complete_apps = ['fts_web']