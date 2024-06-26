# Generated by Django 3.2.21 on 2024-02-21 15:49

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import hoover.search.validators


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('search', '0014_collection_stats'),
    ]

    operations = [
        migrations.CreateModel(
            name='WebDAVPassword',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('password', models.CharField(max_length=256)),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='NextcloudDirectory',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=256)),
                ('path', models.CharField(max_length=512, unique=True)),
                ('modified', models.DateTimeField()),
                ('deleted_from_nextcloud', models.DateTimeField(null=True)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name_plural': 'Nextcloud directories',
            },
        ),
        migrations.CreateModel(
            name='NextcloudCollection',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=256, unique=True, validators=[hoover.search.validators.validate_collection_name])),
                ('process', models.BooleanField(default=True)),
                ('sync', models.BooleanField(default=True)),
                ('ocr_languages', models.CharField(blank=True, default='', max_length=256)),
                ('max_result_window', models.IntegerField(default=100000)),
                ('pdf_preview_enabled', models.BooleanField(default=False)),
                ('thumbnail_generator_enabled', models.BooleanField(default=False)),
                ('image_classification_object_detection_enabled', models.BooleanField(default=False)),
                ('image_classification_classify_images_enabled', models.BooleanField(default=False)),
                ('nlp_language_detection_enabled', models.BooleanField(default=False)),
                ('nlp_fallback_language', models.CharField(default='en', max_length=256)),
                ('nlp_entity_extraction_enabled', models.BooleanField(default=False)),
                ('translation_enabled', models.BooleanField(default=False)),
                ('translation_target_languages', models.CharField(default='en', max_length=256)),
                ('translation_text_length_limit', models.IntegerField(default=400)),
                ('default_table_header', models.CharField(blank=True, default='', max_length=512)),
                ('explode_table_rows', models.BooleanField(default=False)),
                ('s3_blobs_address', models.CharField(blank=True, default='', max_length=512)),
                ('s3_blobs_access_key', models.CharField(blank=True, default='', max_length=512)),
                ('s3_blobs_secret_key', models.CharField(blank=True, default='', max_length=512)),
                ('collection', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='search.collection')),
                ('directory', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to='search.nextclouddirectory', validators=[hoover.search.validators.validate_directory_path])),
            ],
        ),
    ]
