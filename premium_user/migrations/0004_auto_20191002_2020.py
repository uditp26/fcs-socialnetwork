# Generated by Django 2.2.3 on 2019-10-02 14:50

import django.contrib.postgres.fields
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('premium_user', '0003_auto_20191002_2018'),
    ]

    operations = [
        migrations.AlterField(
            model_name='addgroup',
            name='members',
            field=django.contrib.postgres.fields.ArrayField(base_field=models.CharField(blank=True, max_length=50), size=None),
        ),
    ]
