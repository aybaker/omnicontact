# -*- coding: utf-8 -*-
# Generated by Django 1.9.7 on 2019-02-19 13:04
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('ominicontacto_app', '0013_add_callid_calificacion'),
    ]

    operations = [
        migrations.RenameField(
            model_name='grabacion',
            old_name='uid',
            new_name='callid',
        ),
        migrations.RenameField(
            model_name='grabacionmarca',
            old_name='uid',
            new_name='callid',
        ),
    ]
