# Generated by Django 2.2.6 on 2019-10-29 10:53

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('premium_user', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Encryption',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('user', models.CharField(max_length=40)),
                ('publickey', models.CharField(max_length=100000)),
                ('privatekey', models.CharField(max_length=100000)),
            ],
        ),
    ]
