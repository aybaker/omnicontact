# -*- coding: utf-8 -*-
# Generated by Django 1.9.7 on 2019-03-20 13:50
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('ominicontacto_app', '0019_add_opcioncalificacion_formulario'),
    ]

    operations = [
        # Por último elimino el campo formulario en el modelo de campaña
        migrations.RemoveField(
            model_name='campana',
            name='formulario',
        ),
    ]
