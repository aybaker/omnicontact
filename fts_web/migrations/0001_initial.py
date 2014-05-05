# -*- coding: utf-8 -*-
#@PydevCodeAnalysisIgnore
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'GrupoAtencion'
        db.create_table(u'fts_web_grupoatencion', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('nombre', self.gf('django.db.models.fields.CharField')(max_length=128)),
            ('timeout', self.gf('django.db.models.fields.PositiveIntegerField')()),
            ('ring_strategy', self.gf('django.db.models.fields.PositiveIntegerField')(default=0)),
        ))
        db.send_create_signal(u'fts_web', ['GrupoAtencion'])

        # Adding model 'AgenteGrupoAtencion'
        db.create_table(u'fts_web_agentegrupoatencion', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('numero_interno', self.gf('django.db.models.fields.CharField')(max_length=32)),
            ('grupo_atencion', self.gf('django.db.models.fields.related.ForeignKey')(related_name=u'agentes', to=orm['fts_web.GrupoAtencion'])),
        ))
        db.send_create_signal(u'fts_web', ['AgenteGrupoAtencion'])

        # Adding model 'BaseDatosContacto'
        db.create_table(u'fts_web_basedatoscontacto', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('nombre', self.gf('django.db.models.fields.CharField')(max_length=128)),
            ('fecha_alta', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('columnas', self.gf('django.db.models.fields.CharField')(max_length=256, null=True, blank=True)),
            ('archivo_importacion', self.gf('django.db.models.fields.files.FileField')(max_length=100)),
            ('nombre_archivo_importacion', self.gf('django.db.models.fields.CharField')(max_length=256)),
            ('sin_definir', self.gf('django.db.models.fields.BooleanField')(default=True)),
            ('columna_datos', self.gf('django.db.models.fields.PositiveIntegerField')(null=True, blank=True)),
        ))
        db.send_create_signal(u'fts_web', ['BaseDatosContacto'])

        # Adding model 'Contacto'
        db.create_table(u'fts_web_contacto', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('telefono', self.gf('django.db.models.fields.CharField')(max_length=64)),
            ('datos', self.gf('django.db.models.fields.TextField')(null=True, blank=True)),
            ('bd_contacto', self.gf('django.db.models.fields.related.ForeignKey')(related_name=u'contactos', to=orm['fts_web.BaseDatosContacto'])),
        ))
        db.send_create_signal(u'fts_web', ['Contacto'])

        # Adding model 'Campana'
        db.create_table(u'fts_web_campana', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('nombre', self.gf('django.db.models.fields.CharField')(max_length=128)),
            ('estado', self.gf('django.db.models.fields.PositiveIntegerField')(default=1)),
            ('cantidad_canales', self.gf('django.db.models.fields.PositiveIntegerField')()),
            ('cantidad_intentos', self.gf('django.db.models.fields.PositiveIntegerField')()),
            ('segundos_ring', self.gf('django.db.models.fields.PositiveIntegerField')()),
            ('fecha_inicio', self.gf('django.db.models.fields.DateField')()),
            ('fecha_fin', self.gf('django.db.models.fields.DateField')()),
            ('audio_original', self.gf('django.db.models.fields.files.FileField')(max_length=100, null=True, blank=True)),
            ('audio_asterisk', self.gf('django.db.models.fields.files.FileField')(max_length=100, null=True, blank=True)),
            ('bd_contacto', self.gf('django.db.models.fields.related.ForeignKey')(related_name=u'campanas', to=orm['fts_web.BaseDatosContacto'])),
        ))
        db.send_create_signal(u'fts_web', ['Campana'])

        # Adding model 'EventoDeContacto'
        db.create_table(u'fts_web_eventodecontacto', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('campana_id', self.gf('django.db.models.fields.IntegerField')(db_index=True)),
            ('contacto_id', self.gf('django.db.models.fields.IntegerField')(db_index=True)),
            ('timestamp', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('evento', self.gf('django.db.models.fields.SmallIntegerField')(db_index=True)),
            ('dato', self.gf('django.db.models.fields.SmallIntegerField')(null=True)),
        ))
        db.send_create_signal(u'fts_web', ['EventoDeContacto'])

        # Adding model 'Opcion'
        db.create_table(u'fts_web_opcion', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('digito', self.gf('django.db.models.fields.PositiveIntegerField')()),
            ('accion', self.gf('django.db.models.fields.PositiveIntegerField')()),
            ('grupo_atencion', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['fts_web.GrupoAtencion'], null=True, blank=True)),
            ('calificacion', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['fts_web.Calificacion'], null=True, blank=True)),
            ('campana', self.gf('django.db.models.fields.related.ForeignKey')(related_name=u'opciones', to=orm['fts_web.Campana'])),
        ))
        db.send_create_signal(u'fts_web', ['Opcion'])

        # Adding unique constraint on 'Opcion', fields ['digito', 'campana']
        db.create_unique(u'fts_web_opcion', ['digito', 'campana_id'])

        # Adding unique constraint on 'Opcion', fields ['accion', 'campana', 'grupo_atencion']
        db.create_unique(u'fts_web_opcion', ['accion', 'campana_id', 'grupo_atencion_id'])

        # Adding unique constraint on 'Opcion', fields ['accion', 'campana', 'calificacion']
        db.create_unique(u'fts_web_opcion', ['accion', 'campana_id', 'calificacion_id'])

        # Adding model 'Actuacion'
        db.create_table(u'fts_web_actuacion', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('dia_semanal', self.gf('django.db.models.fields.PositiveIntegerField')()),
            ('hora_desde', self.gf('django.db.models.fields.TimeField')()),
            ('hora_hasta', self.gf('django.db.models.fields.TimeField')()),
            ('campana', self.gf('django.db.models.fields.related.ForeignKey')(related_name=u'actuaciones', to=orm['fts_web.Campana'])),
        ))
        db.send_create_signal(u'fts_web', ['Actuacion'])

        # Adding model 'Calificacion'
        db.create_table(u'fts_web_calificacion', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('nombre', self.gf('django.db.models.fields.CharField')(max_length=64)),
            ('campana', self.gf('django.db.models.fields.related.ForeignKey')(related_name=u'calificaciones', to=orm['fts_web.Campana'])),
        ))
        db.send_create_signal(u'fts_web', ['Calificacion'])


    def backwards(self, orm):
        # Removing unique constraint on 'Opcion', fields ['accion', 'campana', 'calificacion']
        db.delete_unique(u'fts_web_opcion', ['accion', 'campana_id', 'calificacion_id'])

        # Removing unique constraint on 'Opcion', fields ['accion', 'campana', 'grupo_atencion']
        db.delete_unique(u'fts_web_opcion', ['accion', 'campana_id', 'grupo_atencion_id'])

        # Removing unique constraint on 'Opcion', fields ['digito', 'campana']
        db.delete_unique(u'fts_web_opcion', ['digito', 'campana_id'])

        # Deleting model 'GrupoAtencion'
        db.delete_table(u'fts_web_grupoatencion')

        # Deleting model 'AgenteGrupoAtencion'
        db.delete_table(u'fts_web_agentegrupoatencion')

        # Deleting model 'BaseDatosContacto'
        db.delete_table(u'fts_web_basedatoscontacto')

        # Deleting model 'Contacto'
        db.delete_table(u'fts_web_contacto')

        # Deleting model 'Campana'
        db.delete_table(u'fts_web_campana')

        # Deleting model 'EventoDeContacto'
        db.delete_table(u'fts_web_eventodecontacto')

        # Deleting model 'Opcion'
        db.delete_table(u'fts_web_opcion')

        # Deleting model 'Actuacion'
        db.delete_table(u'fts_web_actuacion')

        # Deleting model 'Calificacion'
        db.delete_table(u'fts_web_calificacion')


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