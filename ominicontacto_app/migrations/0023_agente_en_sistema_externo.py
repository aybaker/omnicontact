# -*- coding: utf-8 -*-
# Generated by Django 1.9.7 on 2019-05-09 16:54
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('ominicontacto_app', '0022_contacto_id_externo'),
    ]

    operations = [
        migrations.CreateModel(
            name='AgenteEnSistemaExterno',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('id_externo_agente', models.CharField(max_length=128)),
                ('agente', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='ominicontacto_app.AgenteProfile')),
                ('sistema_externo', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='ominicontacto_app.SistemaExterno')),
            ],
        ),
        migrations.AddField(
            model_name='sistemaexterno',
            name='agentes',
            field=models.ManyToManyField(through='ominicontacto_app.AgenteEnSistemaExterno', to='ominicontacto_app.AgenteProfile', verbose_name='Agentes'),
        ),
        migrations.AlterUniqueTogether(
            name='agenteensistemaexterno',
            unique_together=set([('sistema_externo', 'id_externo_agente'), ('sistema_externo', 'agente')]),
        ),
    ]
