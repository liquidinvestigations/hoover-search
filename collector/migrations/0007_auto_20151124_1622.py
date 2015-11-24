# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('collector', '0006_auto_20151123_2254'),
    ]

    operations = [
        migrations.AddField(
            model_name='collection',
            name='loader',
            field=models.CharField(default=b'collector.loaders.collectible.Loader', max_length=2048),
        ),
        migrations.AddField(
            model_name='collection',
            name='options',
            field=models.TextField(default=b'{}'),
        ),
    ]
