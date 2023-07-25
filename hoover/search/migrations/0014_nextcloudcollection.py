# Generated by Django 3.1.3 on 2023-06-23 14:26

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('search', '0013_uploads_squashed_0014_auto_20221214_1723'),
    ]

    operations = [
        migrations.CreateModel(
            name='NextcloudCollection',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('url', models.CharField(max_length=256)),
                ('mount_path', models.CharField(max_length=256)),
                ('username', models.CharField(max_length=256)),
                ('password', models.CharField(max_length=256)),
            ],
        ),
    ]
