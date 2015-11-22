# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('collector', '0003_auto_20151122_1546'),
    ]

    operations = [
        migrations.AddField(
            model_name='collection',
            name='users',
            field=models.ManyToManyField(to=settings.AUTH_USER_MODEL),
        ),
    ]
