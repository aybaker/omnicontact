# -*- coding: utf-8 -*-
# Generated by Django 1.9.7 on 2017-05-24 15:35
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('ominicontacto_app', '0089_campanadialer_reported_by'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='calificacioncliente',
            name='campana',
        ),
        migrations.RemoveField(
            model_name='metadatacliente',
            name='campana',
        ),
        migrations.RemoveField(
            model_name='wombatlog',
            name='campana',
        ),
    ]