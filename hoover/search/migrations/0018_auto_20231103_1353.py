# Generated by Django 3.2.21 on 2023-11-03 13:53

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('search', '0017_webdavpassword'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='nextcloudcollection',
            name='mount_path',
        ),
        migrations.RemoveField(
            model_name='nextcloudcollection',
            name='name',
        ),
        migrations.RemoveField(
            model_name='nextcloudcollection',
            name='password',
        ),
        migrations.RemoveField(
            model_name='nextcloudcollection',
            name='url',
        ),
        migrations.RemoveField(
            model_name='nextcloudcollection',
            name='username',
        ),
        migrations.AddField(
            model_name='nextcloudcollection',
            name='directory',
            field=models.OneToOneField(default='1', on_delete=django.db.models.deletion.CASCADE, to='search.nextclouddirectory'),
            preserve_default=False,
        ),
    ]
