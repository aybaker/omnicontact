# -*- coding: utf-8 -*-
# Generated by Django 1.9.7 on 2016-09-21 14:17
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ominicontacto_app', '0023_auto_20160909_1436'),
    ]

    operations = [
        migrations.RenameField(
            model_name='contacto',
            old_name='email',
            new_name='cuil',
        ),
        migrations.RenameField(
            model_name='contacto',
            old_name='telefono',
            new_name='dni',
        ),
        migrations.AddField(
            model_name='contacto',
            name='fecha_nacimiento',
            field=models.CharField(default='16/10/1988', max_length=128),
            preserve_default=False,
        ),
    ]