# -*- coding: utf-8 -*-
# Generated by Django 1.9.7 on 2019-06-27 19:54
from __future__ import unicode_literals

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('ominicontacto_app', '0031_elimina_campo_gestion_campana'),
    ]

    operations = [
        migrations.CreateModel(
            name='ClienteWebPhoneProfile',
            fields=[
                ('id', models.AutoField(auto_created=True,
                                        primary_key=True,
                                        serialize=False,
                                        verbose_name='ID')),
                ('sip_extension', models.IntegerField(unique=True)),
                ('is_inactive', models.BooleanField(default=False)),
                ('borrado', models.BooleanField(default=False)),
            ],
        ),
        migrations.AddField(
            model_name='user',
            name='is_cliente_webphone',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='clientewebphoneprofile',
            name='user',
            field=models.OneToOneField(on_delete=django.db.models.deletion.CASCADE,
                                       to=settings.AUTH_USER_MODEL),
        ),
    ]
