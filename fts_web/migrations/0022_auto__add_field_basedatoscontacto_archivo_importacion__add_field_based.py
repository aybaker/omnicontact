# -*- coding: utf-8 -*-
# pylint: skip-file

from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding field 'BaseDatosContacto.archivo_importacion'
        db.add_column(u'fts_web_basedatoscontacto', 'archivo_importacion',
                      self.gf('django.db.models.fields.files.FileField')(default=1, max_length=100),
                      keep_default=False)

        # Adding field 'BaseDatosContacto.sin_definir'
        db.add_column(u'fts_web_basedatoscontacto', 'sin_definir',
                      self.gf('django.db.models.fields.BooleanField')(default=True),
                      keep_default=False)

        # Adding field 'BaseDatosContacto.columna_datos'
        db.add_column(u'fts_web_basedatoscontacto', 'columna_datos',
                      self.gf('django.db.models.fields.PositiveIntegerField')(null=True, blank=True),
                      keep_default=False)


    def backwards(self, orm):
        # Deleting field 'BaseDatosContacto.archivo_importacion'
        db.delete_column(u'fts_web_basedatoscontacto', 'archivo_importacion')

        # Deleting field 'BaseDatosContacto.sin_definir'
        db.delete_column(u'fts_web_basedatoscontacto', 'sin_definir')

        # Deleting field 'BaseDatosContacto.columna_datos'
        db.delete_column(u'fts_web_basedatoscontacto', 'columna_datos')


    models = {
        u'fts_web.actuacion': {
            'Meta': {'object_name': 'Actuacion'},
            'campana': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "u'actuaciones'", 'to': u"orm['fts_web.Campana']"}),
            'dia_semanal': ('django.db.models.fields.PositiveIntegerField', [], {}),
            'hora_desde': ('django.db.models.fields.TimeField', [], {}),
            'hora_hasta': ('django.db.models.fields.TimeField', [], {}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'})
        },
        u'fts_web.agentegrupoatencion': {
            'Meta': {'object_name': 'AgenteGrupoAtencion'},
            'grupo_atencion': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "u'agentes'", 'to': u"orm['fts_web.GrupoAtencion']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'numero_interno': ('django.db.models.fields.PositiveIntegerField', [], {})
        },
        u'fts_web.basedatoscontacto': {
            'Meta': {'object_name': 'BaseDatosContacto'},
            'archivo_importacion': ('django.db.models.fields.files.FileField', [], {'max_length': '100'}),
            'columna_datos': ('django.db.models.fields.PositiveIntegerField', [], {'null': 'True', 'blank': 'True'}),
            'columnas': ('django.db.models.fields.CharField', [], {'max_length': '256', 'null': 'True', 'blank': 'True'}),
            'fecha_alta': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'nombre': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'sin_definir': ('django.db.models.fields.BooleanField', [], {'default': 'True'})
        },
        u'fts_web.campana': {
            'Meta': {'object_name': 'Campana'},
            'bd_contacto': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "u'campanas'", 'to': u"orm['fts_web.BaseDatosContacto']"}),
            'cantidad_canales': ('django.db.models.fields.PositiveIntegerField', [], {}),
            'cantidad_intentos': ('django.db.models.fields.PositiveIntegerField', [], {}),
            'estado': ('django.db.models.fields.PositiveIntegerField', [], {'default': '1'}),
            'fecha_fin': ('django.db.models.fields.DateTimeField', [], {}),
            'fecha_inicio': ('django.db.models.fields.DateTimeField', [], {}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'nombre': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'reproduccion': ('django.db.models.fields.files.FileField', [], {'max_length': '100'}),
            'segundos_ring': ('django.db.models.fields.PositiveIntegerField', [], {})
        },
        u'fts_web.contacto': {
            'Meta': {'object_name': 'Contacto'},
            'bd_contacto': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "u'contactos'", 'to': u"orm['fts_web.BaseDatosContacto']"}),
            'datos': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
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
        u'fts_web.opcion': {
            'Meta': {'unique_together': "((u'digito', u'campana'),)", 'object_name': 'Opcion'},
            'accion': ('django.db.models.fields.PositiveIntegerField', [], {}),
            'campana': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "u'opciones'", 'to': u"orm['fts_web.Campana']"}),
            'digito': ('django.db.models.fields.PositiveIntegerField', [], {}),
            'grupo_atencion': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['fts_web.GrupoAtencion']", 'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'})
        }
    }

    complete_apps = ['fts_web']