# Generated by Django 2.2.7 on 2020-04-30 19:30

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ominicontacto_app', '0047_delete_autopause_autoattendics'),
    ]

    operations = [
        migrations.AddField(
            model_name='campana',
            name='campos_bd_no_editables',
            field=models.CharField(default='', max_length=512),
        ),
        migrations.AddField(
            model_name='campana',
            name='campos_bd_ocultos',
            field=models.CharField(default='', max_length=512),
        ),
    ]
