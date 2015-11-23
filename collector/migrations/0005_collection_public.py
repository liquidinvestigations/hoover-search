# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('collector', '0004_collection_users'),
    ]

    operations = [
        migrations.AddField(
            model_name='collection',
            name='public',
            field=models.BooleanField(default=False),
        ),
    ]
