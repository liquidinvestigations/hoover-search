# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Document',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('hash', models.CharField(max_length=300)),
                ('url', models.URLField(max_length=2048)),
                ('indexed', models.BooleanField(default=False)),
                ('index_time', models.DateTimeField(null=True, blank=True)),
                ('title', models.CharField(max_length=2048, blank=True)),
                ('slug', models.CharField(unique=True, max_length=256)),
            ],
        ),
    ]
