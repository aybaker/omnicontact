# -*- coding: utf-8 -*-
# Generated by Django 1.9.7 on 2016-09-29 18:28
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('ominicontacto_app', '0027_auto_20160929_1518'),
    ]

    operations = [
        migrations.RenameField(
            model_name='formulariodatoventa',
            old_name='domicilio_labral',
            new_name='domicilio_laboral',
        ),
    ]