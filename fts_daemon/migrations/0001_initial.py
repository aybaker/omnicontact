# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='EventoDeContacto',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('campana_id', models.IntegerField(db_index=True)),
                ('contacto_id', models.IntegerField(db_index=True)),
                ('timestamp', models.DateTimeField(auto_now_add=True)),
                ('evento', models.SmallIntegerField(db_index=True)),
                ('dato', models.SmallIntegerField(db_index=True)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
    ]
