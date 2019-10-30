# Generated by Django 2.2.6 on 2019-10-30 09:51

from django.conf import settings
import django.contrib.postgres.fields
from django.db import migrations, models
import django.db.models.deletion
import phonenumber_field.modelfields


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='AddGroup',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('admin', models.CharField(max_length=30)),
                ('name', models.CharField(max_length=30)),
                ('gtype', models.SmallIntegerField()),
                ('price', models.FloatField()),
                ('members', django.contrib.postgres.fields.ArrayField(base_field=models.CharField(max_length=50), null=True, size=None)),
            ],
        ),
        migrations.CreateModel(
            name='Encryption',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('user', models.CharField(max_length=40)),
                ('publickey', models.CharField(max_length=100000)),
                ('privatekey', models.CharField(max_length=100000)),
            ],
        ),
        migrations.CreateModel(
            name='Group',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('admin', models.CharField(max_length=30)),
                ('group_list', django.contrib.postgres.fields.ArrayField(base_field=models.CharField(max_length=50), null=True, size=None)),
            ],
        ),
        migrations.CreateModel(
            name='GroupPlan',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('customer', models.CharField(max_length=30)),
                ('recharge_on', models.DateTimeField()),
                ('plantype', models.CharField(max_length=30)),
                ('noofgroup', models.FloatField()),
            ],
        ),
        migrations.CreateModel(
            name='GroupRequest',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('admin', models.CharField(max_length=30)),
                ('name', models.CharField(max_length=30)),
                ('status', models.SmallIntegerField()),
                ('members', django.contrib.postgres.fields.ArrayField(base_field=models.CharField(max_length=50, null=True), size=None)),
            ],
        ),
        migrations.CreateModel(
            name='Message',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('sender', models.CharField(max_length=40)),
                ('receiver', models.CharField(max_length=40)),
                ('messages', django.contrib.postgres.fields.ArrayField(base_field=models.CharField(max_length=1000, null=True), size=None)),
                ('timestamp', django.contrib.postgres.fields.ArrayField(base_field=models.DateTimeField(), size=None)),
            ],
        ),
        migrations.CreateModel(
            name='PremiumUser',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date_of_birth', models.DateField()),
                ('gender', models.SmallIntegerField()),
                ('phone', phonenumber_field.modelfields.PhoneNumberField(blank=True, max_length=128, region=None)),
                ('email', models.EmailField(max_length=254)),
                ('subscription', models.SmallIntegerField(default=0)),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]
