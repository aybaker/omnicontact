# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models
from django.db import connection
from django.conf import settings


class Migration(SchemaMigration):

    def forwards(self, orm):
        pg = 'django.db.backends.postgresql_psycopg2'
        if settings.DATABASES['default']['ENGINE'] != pg:
            print("Ignorando migracion: BD no es postgresql")
            return

        cursor = connection.cursor()

        # Crea tabla consultas_sms
        sql = """
        CREATE TABLE consultas_sms (
            fecha timestamp(0) WITHOUT time zone NOT NULL DEFAULT LOCALTIMESTAMP(0),
            token varchar(50) NOT NULL,
            metadatos varchar(200) NOT NULL,
		    estado varchar(255) NOT NULL,
		    userfield varchar(20) NOT NULL,
		    password varchar(20) NOT NULL,
		    datos1 text NOT NULL,
		    datos2 text NOT NULL,
		    datos3 text NOT NULL,
  		    datos4 text NOT NULL,
		    datos5 text NOT NULL,
		    datos6 text NOT NULL,
		    datos7 text NOT NULL,
		    datos8 text NOT NULL,
		    datos9 text NOT NULL,
		    datos10 text NOT NULL,
		    PRIMARY KEY (token)
        )
        """
        cursor.execute(sql)

        # Crea indices para la tabla consultas_sms
        sql = """
        CREATE INDEX consultas_sms_token ON consultas_sms(token)
        """
        cursor.execute(sql)

        sql = """
        CREATE INDEX consultas_sms_fecha ON consultas_sms(fecha)
        """
        cursor.execute(sql)


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
        u'fts_web.actuacionsms': {
            'Meta': {'object_name': 'ActuacionSms'},
            'campana_sms': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "u'actuaciones'", 'to': u"orm['fts_web.CampanaSms']"}),
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
        u'fts_web.agregaciondeeventodecontacto': {
            'Meta': {'object_name': 'AgregacionDeEventoDeContacto'},
            'campana_id': ('django.db.models.fields.IntegerField', [], {'db_index': 'True'}),
            'cantidad_finalizados': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'cantidad_intentos': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'cantidad_opcion_0': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'cantidad_opcion_1': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'cantidad_opcion_2': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'cantidad_opcion_3': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'cantidad_opcion_4': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'cantidad_opcion_5': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'cantidad_opcion_6': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'cantidad_opcion_7': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'cantidad_opcion_8': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'cantidad_opcion_9': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'numero_intento': ('django.db.models.fields.IntegerField', [], {}),
            'timestamp_ultima_actualizacion': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'timestamp_ultimo_evento': ('django.db.models.fields.DateTimeField', [], {}),
            'tipo_agregacion': ('django.db.models.fields.IntegerField', [], {'null': 'True'})
        },
        u'fts_web.archivodeaudio': {
            'Meta': {'object_name': 'ArchivoDeAudio'},
            'audio_asterisk': ('django.db.models.fields.files.FileField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'audio_original': ('django.db.models.fields.files.FileField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'borrado': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'descripcion': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'})
        },
        u'fts_web.audiodecampana': {
            'Meta': {'ordering': "[u'orden']", 'unique_together': "((u'orden', u'campana'),)", 'object_name': 'AudioDeCampana'},
            'archivo_de_audio': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['fts_web.ArchivoDeAudio']", 'null': 'True', 'blank': 'True'}),
            'audio_asterisk': ('django.db.models.fields.files.FileField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'audio_descripcion': ('django.db.models.fields.CharField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'audio_original': ('django.db.models.fields.files.FileField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'campana': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "u'audios_de_campana'", 'to': u"orm['fts_web.Campana']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'orden': ('django.db.models.fields.PositiveIntegerField', [], {}),
            'tts': ('django.db.models.fields.CharField', [], {'max_length': '128', 'null': 'True', 'blank': 'True'})
        },
        u'fts_web.basedatoscontacto': {
            'Meta': {'object_name': 'BaseDatosContacto'},
            'archivo_importacion': ('django.db.models.fields.files.FileField', [], {'max_length': '256'}),
            'cantidad_contactos': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            'estado': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            'fecha_alta': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'metadata': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
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
            'Meta': {'ordering': "[u'pk']", 'object_name': 'Campana'},
            'accion_contestador': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            'bd_contacto': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "u'campanas'", 'null': 'True', 'to': u"orm['fts_web.BaseDatosContacto']"}),
            'cantidad_canales': ('django.db.models.fields.PositiveIntegerField', [], {}),
            'cantidad_intentos': ('django.db.models.fields.PositiveIntegerField', [], {}),
            'duracion_de_audio': ('django.db.models.fields.TimeField', [], {'null': 'True', 'blank': 'True'}),
            'es_template': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'estadisticas': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'estado': ('django.db.models.fields.PositiveIntegerField', [], {'default': '1'}),
            'fecha_fin': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'fecha_inicio': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'nombre': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'segundos_ring': ('django.db.models.fields.PositiveIntegerField', [], {})
        },
        u'fts_web.campanasms': {
            'Meta': {'ordering': "[u'pk']", 'object_name': 'CampanaSms'},
            'bd_contacto': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "u'campanasmss'", 'null': 'True', 'to': u"orm['fts_web.BaseDatosContacto']"}),
            'cantidad_chips': ('django.db.models.fields.PositiveIntegerField', [], {}),
            'estado': ('django.db.models.fields.PositiveIntegerField', [], {'default': '1'}),
            'fecha_fin': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'fecha_inicio': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'identificador_campana_sms': ('django.db.models.fields.PositiveIntegerField', [], {'unique': 'True'}),
            'nombre': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'template_mensaje': ('django.db.models.fields.TextField', [], {}),
            'template_mensaje_alternativo': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'template_mensaje_opcional': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'tiene_respuesta': ('django.db.models.fields.BooleanField', [], {})
        },
        u'fts_web.contacto': {
            'Meta': {'object_name': 'Contacto'},
            'bd_contacto': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "u'contactos'", 'to': u"orm['fts_web.BaseDatosContacto']"}),
            'datos': ('django.db.models.fields.TextField', [], {}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'})
        },
        u'fts_web.derivacionexterna': {
            'Meta': {'object_name': 'DerivacionExterna'},
            'borrado': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'dial_string': ('django.db.models.fields.CharField', [], {'max_length': '256'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'nombre': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'tipo_derivacion': ('django.db.models.fields.PositiveIntegerField', [], {'default': '1'})
        },
        u'fts_web.duraciondellamada': {
            'Meta': {'object_name': 'DuracionDeLlamada'},
            'campana': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['fts_web.Campana']"}),
            'duracion_en_segundos': ('django.db.models.fields.PositiveIntegerField', [], {}),
            'eventos_del_contacto': ('django.db.models.fields.TextField', [], {}),
            'fecha_hora_llamada': ('django.db.models.fields.DateTimeField', [], {}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'numero_telefono': ('django.db.models.fields.CharField', [], {'max_length': '20'})
        },
        u'fts_web.grupoatencion': {
            'Meta': {'object_name': 'GrupoAtencion'},
            'borrado': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
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
            'derivacion_externa': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['fts_web.DerivacionExterna']", 'null': 'True', 'blank': 'True'}),
            'digito': ('django.db.models.fields.PositiveIntegerField', [], {}),
            'grupo_atencion': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['fts_web.GrupoAtencion']", 'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'})
        },
        u'fts_web.opcionsms': {
            'Meta': {'object_name': 'OpcionSms'},
            'campana_sms': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "u'opcionsmss'", 'to': u"orm['fts_web.CampanaSms']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'respuesta': ('django.db.models.fields.CharField', [], {'max_length': '64'}),
            'respuesta_descripcion': ('django.db.models.fields.CharField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'})
        }
    }

    complete_apps = ['fts_web']