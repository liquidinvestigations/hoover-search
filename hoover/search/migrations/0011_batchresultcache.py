# Generated by Django 3.1.3 on 2022-11-22 19:33

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import hoover.search.models


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('search', '0010_auto_20211022_0641'),
    ]

    operations = [
        migrations.CreateModel(
            name='BatchResultCache',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('args', models.JSONField()),
                ('result', models.JSONField(default=None, null=True)),
                ('task_id', models.CharField(default=hoover.search.models.random_uuid, max_length=51, unique=True)),
                ('date_created', models.DateTimeField(auto_now_add=True)),
                ('date_modified', models.DateTimeField(auto_now=True)),
                ('date_started', models.DateTimeField(null=True)),
                ('date_finished', models.DateTimeField(null=True)),
                ('collections', models.ManyToManyField(to='search.Collection')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]
