# -*- coding: utf-8 -*-
# Generated by Django 1.9.7 on 2018-06-19 21:43
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('ominicontacto_app', '0177_adiciona_audios_queue'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='wombatlog',
            name='agente',
        ),
        migrations.RemoveField(
            model_name='wombatlog',
            name='campana',
        ),
        migrations.RemoveField(
            model_name='wombatlog',
            name='contacto',
        ),
        migrations.RemoveField(
            model_name='calificacioncliente',
            name='wombat_id',
        ),
        migrations.RemoveField(
            model_name='historicalcalificacioncliente',
            name='wombat_id',
        ),
        migrations.DeleteModel(
            name='WombatLog',
        ),
    ]
