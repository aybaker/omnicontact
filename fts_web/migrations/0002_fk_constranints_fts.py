# -*- coding: utf-8 -*-
#@PydevCodeAnalysisIgnore

from __future__ import print_function

from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models
from django.conf import settings


class Migration(SchemaMigration):

    def forwards(self, orm):

        if not settings.FTS_TESTING_MODE:
            print("Ignorando migracion: no en FTS_TESTING_MODE")
            return

        pg = 'django.db.backends.postgresql_psycopg2'
        if settings.DATABASES['default']['ENGINE'] != pg:
            print("Ignorando migracion: BD no es postgresql")
            return

        sql = """
        ALTER TABLE fts_web_eventodecontacto
            ADD CONSTRAINT contacto_id_fk
                FOREIGN KEY (contacto_id)
                    REFERENCES fts_web_contacto (id) MATCH FULL;
        """
        db.execute(sql)

        sql = """
        ALTER TABLE fts_web_eventodecontacto
            ADD CONSTRAINT campana_id_fk
                FOREIGN KEY (campana_id)
                    REFERENCES fts_web_campana (id) MATCH FULL;
        """
        db.execute(sql)

    def backwards(self, orm):
        pass

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
            'numero_interno': ('django.db.models.fields.CharField', [], {'max_length': '32'})
        },
        u'fts_web.basedatoscontacto': {
            'Meta': {'object_name': 'BaseDatosContacto'},
            'archivo_importacion': ('django.db.models.fields.files.FileField', [], {'max_length': '100'}),
            'columna_datos': ('django.db.models.fields.PositiveIntegerField', [], {'null': 'True', 'blank': 'True'}),
            'columnas': ('django.db.models.fields.CharField', [], {'max_length': '256', 'null': 'True', 'blank': 'True'}),
            'fecha_alta': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'nombre': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'nombre_archivo_importacion': ('django.db.models.fields.CharField', [], {'max_length': '256'}),
            'sin_definir': ('django.db.models.fields.BooleanField', [], {'default': 'True'})
        },
        u'fts_web.calificacion': {
            'Meta': {'ordering': "[u'nombre']", 'object_name': 'Calificacion'},
            'campana': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "u'calificaciones'", 'to': u"orm['fts_web.Campana']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'nombre': ('django.db.models.fields.CharField', [], {'max_length': '64'})
        },
        u'fts_web.campana': {
            'Meta': {'object_name': 'Campana'},
            'audio_asterisk': ('django.db.models.fields.files.FileField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'audio_original': ('django.db.models.fields.files.FileField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'bd_contacto': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "u'campanas'", 'to': u"orm['fts_web.BaseDatosContacto']"}),
            'cantidad_canales': ('django.db.models.fields.PositiveIntegerField', [], {}),
            'cantidad_intentos': ('django.db.models.fields.PositiveIntegerField', [], {}),
            'estado': ('django.db.models.fields.PositiveIntegerField', [], {'default': '1'}),
            'fecha_fin': ('django.db.models.fields.DateField', [], {}),
            'fecha_inicio': ('django.db.models.fields.DateField', [], {}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'nombre': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'segundos_ring': ('django.db.models.fields.PositiveIntegerField', [], {})
        },
        u'fts_web.contacto': {
            'Meta': {'object_name': 'Contacto'},
            'bd_contacto': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "u'contactos'", 'to': u"orm['fts_web.BaseDatosContacto']"}),
            'datos': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'telefono': ('django.db.models.fields.CharField', [], {'max_length': '64'})
        },
        u'fts_web.eventodecontacto': {
            'Meta': {'object_name': 'EventoDeContacto'},
            'campana_id': ('django.db.models.fields.IntegerField', [], {'db_index': 'True'}),
            'contacto_id': ('django.db.models.fields.IntegerField', [], {'db_index': 'True'}),
            'dato': ('django.db.models.fields.SmallIntegerField', [], {'null': 'True'}),
            'evento': ('django.db.models.fields.SmallIntegerField', [], {'db_index': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'timestamp': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'})
        },
        u'fts_web.grupoatencion': {
            'Meta': {'object_name': 'GrupoAtencion'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'nombre': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'ring_strategy': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            'timeout': ('django.db.models.fields.PositiveIntegerField', [], {})
        },
        u'fts_web.opcion': {
            'Meta': {'unique_together': "((u'digito', u'campana'), (u'accion', u'campana', u'grupo_atencion'), (u'accion', u'campana', u'calificacion'))", 'object_name': 'Opcion'},
            'accion': ('django.db.models.fields.PositiveIntegerField', [], {}),
            'calificacion': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['fts_web.Calificacion']", 'null': 'True', 'blank': 'True'}),
            'campana': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "u'opciones'", 'to': u"orm['fts_web.Campana']"}),
            'digito': ('django.db.models.fields.PositiveIntegerField', [], {}),
            'grupo_atencion': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['fts_web.GrupoAtencion']", 'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'})
        }
    }

    complete_apps = ['fts_web']