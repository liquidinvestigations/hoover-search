# Generated by Django 3.1.3 on 2022-11-30 15:33

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('search', '0016_upload_poll_task'),
    ]

    operations = [
        migrations.AddField(
            model_name='upload',
            name='directory_path',
            field=models.CharField(default='N/A', max_length=256),
            preserve_default=False,
        ),
    ]
