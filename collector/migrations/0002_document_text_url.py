# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('collector', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='document',
            name='text_url',
            field=models.URLField(default='', max_length=2048),
            preserve_default=False,
        ),
    ]
