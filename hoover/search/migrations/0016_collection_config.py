# Generated by Django 3.2.17 on 2023-02-10 15:55

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('search', '0015_collection_stats'),
    ]

    operations = [
        migrations.AddField(
            model_name='collection',
            name='config',
            field=models.JSONField(default=dict),
        ),
    ]
