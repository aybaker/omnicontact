# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Actuacion',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('dia_semanal', models.PositiveIntegerField(choices=[(0, 'LUNES'), (1, 'MARTES'), (2, 'MIERCOLES'), (3, 'JUEVES'), (4, 'VIERNES'), (5, 'SABADO'), (6, 'DOMINGO')])),
                ('hora_desde', models.TimeField()),
                ('hora_hasta', models.TimeField()),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='ActuacionSms',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('dia_semanal', models.PositiveIntegerField(choices=[(0, 'LUNES'), (1, 'MARTES'), (2, 'MIERCOLES'), (3, 'JUEVES'), (4, 'VIERNES'), (5, 'SABADO'), (6, 'DOMINGO')])),
                ('hora_desde', models.TimeField()),
                ('hora_hasta', models.TimeField()),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='AgenteGrupoAtencion',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('numero_interno', models.CharField(max_length=32)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='AgregacionDeEventoDeContacto',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('campana_id', models.IntegerField(db_index=True)),
                ('numero_intento', models.IntegerField()),
                ('cantidad_intentos', models.IntegerField(default=0)),
                ('cantidad_finalizados', models.IntegerField(default=0)),
                ('cantidad_opcion_0', models.IntegerField(default=0)),
                ('cantidad_opcion_1', models.IntegerField(default=0)),
                ('cantidad_opcion_2', models.IntegerField(default=0)),
                ('cantidad_opcion_3', models.IntegerField(default=0)),
                ('cantidad_opcion_4', models.IntegerField(default=0)),
                ('cantidad_opcion_5', models.IntegerField(default=0)),
                ('cantidad_opcion_6', models.IntegerField(default=0)),
                ('cantidad_opcion_7', models.IntegerField(default=0)),
                ('cantidad_opcion_8', models.IntegerField(default=0)),
                ('cantidad_opcion_9', models.IntegerField(default=0)),
                ('timestamp_ultima_actualizacion', models.DateTimeField(auto_now_add=True)),
                ('timestamp_ultimo_evento', models.DateTimeField()),
                ('tipo_agregacion', models.IntegerField(null=True)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='ArchivoDeAudio',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('descripcion', models.CharField(max_length=100)),
                ('audio_original', models.FileField(null=True, upload_to=b'', blank=True)),
                ('audio_asterisk', models.FileField(null=True, upload_to=b'', blank=True)),
                ('borrado', models.BooleanField(default=False, editable=False)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='AudioDeCampana',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('orden', models.PositiveIntegerField()),
                ('audio_descripcion', models.CharField(max_length=100, null=True, blank=True)),
                ('audio_original', models.FileField(null=True, upload_to=b'', blank=True)),
                ('audio_asterisk', models.FileField(null=True, upload_to=b'', blank=True)),
                ('tts', models.CharField(max_length=128, null=True, blank=True)),
                ('tts_mensaje', models.TextField(null=True, blank=True)),
                ('archivo_de_audio', models.ForeignKey(blank=True, to='fts_web.ArchivoDeAudio', null=True)),
            ],
            options={
                'ordering': ['orden'],
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='BaseDatosContacto',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('nombre', models.CharField(max_length=128)),
                ('fecha_alta', models.DateTimeField(auto_now_add=True)),
                ('archivo_importacion', models.FileField(max_length=256, upload_to=b'')),
                ('nombre_archivo_importacion', models.CharField(max_length=256)),
                ('metadata', models.TextField(null=True, blank=True)),
                ('sin_definir', models.BooleanField(default=True)),
                ('cantidad_contactos', models.PositiveIntegerField(default=0)),
                ('estado', models.PositiveIntegerField(default=0, choices=[(0, 'En Definici\xf3n'), (1, 'Definida'), (2, 'En Depuracion'), (3, 'Depurada')])),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Calificacion',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('nombre', models.CharField(max_length=64)),
            ],
            options={
                'ordering': ['nombre'],
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Campana',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('nombre', models.CharField(max_length=128)),
                ('fecha_inicio', models.DateField(null=True, blank=True)),
                ('fecha_fin', models.DateField(null=True, blank=True)),
                ('estado', models.PositiveIntegerField(default=1, choices=[(1, '(en definicion)'), (2, 'Activa'), (3, 'Pausada'), (4, 'Finalizada'), (5, 'Depurada'), (6, 'Borrada'), (7, '(Template en definicion)'), (8, 'Template Activo'), (9, 'Template Borrado')])),
                ('cantidad_canales', models.PositiveIntegerField()),
                ('cantidad_intentos', models.PositiveIntegerField()),
                ('segundos_ring', models.PositiveIntegerField()),
                ('duracion_de_audio', models.TimeField(null=True, blank=True)),
                ('estadisticas', models.TextField(null=True, blank=True)),
                ('es_template', models.BooleanField(default=False)),
                ('accion_contestador', models.PositiveIntegerField(default=0, choices=[(0, 'No hacer nada'), (1, 'Detectar contestador'), (2, 'Detectar y evitar contestador')])),
                ('bd_contacto', models.ForeignKey(related_name='campanas', blank=True, to='fts_web.BaseDatosContacto', null=True)),
            ],
            options={
                'ordering': ['pk'],
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='CampanaSms',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('nombre', models.CharField(max_length=128)),
                ('fecha_inicio', models.DateField(null=True, blank=True)),
                ('fecha_fin', models.DateField(null=True, blank=True)),
                ('estado', models.PositiveIntegerField(default=1, choices=[(1, '(en definicion)'), (2, 'Confirmada'), (3, 'Pausada')])),
                ('cantidad_chips', models.PositiveIntegerField()),
                ('template_mensaje', models.TextField()),
                ('template_mensaje_opcional', models.TextField(null=True, blank=True)),
                ('template_mensaje_alternativo', models.TextField(null=True, blank=True)),
                ('tiene_respuesta', models.BooleanField(default=False)),
                ('identificador_campana_sms', models.PositiveIntegerField(unique=True)),
                ('bd_contacto', models.ForeignKey(related_name='campanasmss', blank=True, to='fts_web.BaseDatosContacto', null=True)),
            ],
            options={
                'ordering': ['pk'],
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Contacto',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('datos', models.TextField()),
                ('bd_contacto', models.ForeignKey(related_name='contactos', to='fts_web.BaseDatosContacto')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='DerivacionExterna',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('tipo_derivacion', models.PositiveIntegerField(default=1, choices=[(1, 'DIAL'), (2, 'GOTO')])),
                ('nombre', models.CharField(max_length=128)),
                ('dial_string', models.CharField(max_length=256)),
                ('borrado', models.BooleanField(default=False, editable=False)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='DuracionDeLlamada',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('numero_telefono', models.CharField(max_length=20)),
                ('fecha_hora_llamada', models.DateTimeField()),
                ('duracion_en_segundos', models.PositiveIntegerField()),
                ('eventos_del_contacto', models.TextField()),
                ('campana', models.ForeignKey(to='fts_web.Campana')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='GrupoAtencion',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('nombre', models.CharField(max_length=128)),
                ('timeout', models.PositiveIntegerField()),
                ('ring_strategy', models.PositiveIntegerField(default=0, choices=[(0, 'RINGALL'), (1, 'RRMEMORY')])),
                ('borrado', models.BooleanField(default=False, editable=False)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Opcion',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('digito', models.PositiveIntegerField(choices=[(0, '0'), (1, '1'), (2, '2'), (3, '3'), (4, '4'), (5, '5'), (6, '6'), (7, '7'), (8, '8'), (9, '9')])),
                ('accion', models.PositiveIntegerField(choices=[(0, 'DERIVAR GRUPO ATENCION'), (1, 'DERIVAR DERIVACION EXTERNA'), (2, 'CALIFICAR'), (4, 'REPETIR')])),
                ('calificacion', models.ForeignKey(blank=True, to='fts_web.Calificacion', null=True)),
                ('campana', models.ForeignKey(related_name='opciones', to='fts_web.Campana')),
                ('derivacion_externa', models.ForeignKey(blank=True, to='fts_web.DerivacionExterna', null=True)),
                ('grupo_atencion', models.ForeignKey(blank=True, to='fts_web.GrupoAtencion', null=True)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='OpcionSms',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('respuesta', models.CharField(max_length=64)),
                ('respuesta_descripcion', models.CharField(max_length=100, null=True, blank=True)),
                ('campana_sms', models.ForeignKey(related_name='opcionsmss', to='fts_web.CampanaSms')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.AlterUniqueTogether(
            name='opcion',
            unique_together=set([('accion', 'campana', 'grupo_atencion'), ('accion', 'campana', 'calificacion'), ('digito', 'campana')]),
        ),
        migrations.AddField(
            model_name='calificacion',
            name='campana',
            field=models.ForeignKey(related_name='calificaciones', to='fts_web.Campana'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='audiodecampana',
            name='campana',
            field=models.ForeignKey(related_name='audios_de_campana', to='fts_web.Campana'),
            preserve_default=True,
        ),
        migrations.AlterUniqueTogether(
            name='audiodecampana',
            unique_together=set([('orden', 'campana')]),
        ),
        migrations.AddField(
            model_name='agentegrupoatencion',
            name='grupo_atencion',
            field=models.ForeignKey(related_name='agentes', to='fts_web.GrupoAtencion'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='actuacionsms',
            name='campana_sms',
            field=models.ForeignKey(related_name='actuaciones', to='fts_web.CampanaSms'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='actuacion',
            name='campana',
            field=models.ForeignKey(related_name='actuaciones', to='fts_web.Campana'),
            preserve_default=True,
        ),
    ]
