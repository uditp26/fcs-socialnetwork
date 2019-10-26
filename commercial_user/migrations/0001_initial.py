# Generated by Django 2.2.5 on 2019-10-25 20:13

import django.contrib.postgres.fields
from django.db import migrations, models
import phonenumber_field.modelfields


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='CommercialUser',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date_of_birth', models.DateField()),
                ('gender', models.SmallIntegerField()),
                ('phone', phonenumber_field.modelfields.PhoneNumberField(blank=True, max_length=128, region=None)),
                ('email', models.EmailField(max_length=254)),
                ('subscription_paid', models.BooleanField(default=False)),
                ('statusofrequest', models.SmallIntegerField(default=1)),
            ],
        ),
        migrations.CreateModel(
            name='Pages',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('username', models.CharField(max_length=30)),
                ('title', django.contrib.postgres.fields.ArrayField(base_field=models.CharField(max_length=50, null=True), size=None)),
                ('description', django.contrib.postgres.fields.ArrayField(base_field=models.CharField(max_length=250, null=True), size=None)),
                ('page_link', django.contrib.postgres.fields.ArrayField(base_field=models.CharField(max_length=100, null=True), size=None)),
            ],
        ),
    ]
