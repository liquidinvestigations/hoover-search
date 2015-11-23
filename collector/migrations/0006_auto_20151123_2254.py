# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('collector', '0005_collection_public'),
    ]

    operations = [
        migrations.AlterField(
            model_name='collection',
            name='users',
            field=models.ManyToManyField(to=settings.AUTH_USER_MODEL, blank=True),
        ),
    ]
