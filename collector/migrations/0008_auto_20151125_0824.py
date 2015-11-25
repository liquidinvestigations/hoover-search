# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('collector', '0007_auto_20151124_1622'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='document',
            name='collection',
        ),
        migrations.DeleteModel(
            name='Document',
        ),
    ]
