# Generated by Django 2.2.3 on 2019-10-02 15:23

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('premium_user', '0009_auto_20191002_2051'),
    ]

    operations = [
        migrations.AlterField(
            model_name='addgroup',
            name='admin',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL),
        ),
    ]
