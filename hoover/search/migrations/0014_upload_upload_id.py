# Generated by Django 3.1.3 on 2022-11-02 09:28

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('search', '0013_upload'),
    ]

    operations = [
        migrations.AddField(
            model_name='upload',
            name='upload_id',
            field=models.UUIDField(null=True),
        ),
    ]