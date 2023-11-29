# Generated by Django 3.2.21 on 2023-11-15 14:00

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('search', '0018_auto_20231103_1353'),
    ]

    operations = [
        migrations.AddField(
            model_name='nextcloudcollection',
            name='default_table_header',
            field=models.CharField(default='', max_length=512),
        ),
        migrations.AddField(
            model_name='nextcloudcollection',
            name='explode_table_rows',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='nextcloudcollection',
            name='image_classification_classify_images_enabled',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='nextcloudcollection',
            name='image_classification_object_detection_enabled',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='nextcloudcollection',
            name='max_result_window',
            field=models.IntegerField(default=100000),
        ),
        migrations.AddField(
            model_name='nextcloudcollection',
            name='nlp_entity_extraction_enabled',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='nextcloudcollection',
            name='nlp_fallback_language',
            field=models.CharField(default='en', max_length=256),
        ),
        migrations.AddField(
            model_name='nextcloudcollection',
            name='nlp_language_detection_enabled',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='nextcloudcollection',
            name='ocr_languages',
            field=models.CharField(default='', max_length=256),
        ),
        migrations.AddField(
            model_name='nextcloudcollection',
            name='pdf_preview_enabled',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='nextcloudcollection',
            name='process',
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name='nextcloudcollection',
            name='s3_blobs_access_key',
            field=models.CharField(default='', max_length=512),
        ),
        migrations.AddField(
            model_name='nextcloudcollection',
            name='s3_blobs_address',
            field=models.CharField(default='', max_length=512),
        ),
        migrations.AddField(
            model_name='nextcloudcollection',
            name='s3_blobs_secret_key',
            field=models.CharField(default='', max_length=512),
        ),
        migrations.AddField(
            model_name='nextcloudcollection',
            name='sync',
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name='nextcloudcollection',
            name='thumbnail_generator_enabled',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='nextcloudcollection',
            name='translation_enabled',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='nextcloudcollection',
            name='translation_target_languages',
            field=models.CharField(default='en', max_length=256),
        ),
        migrations.AddField(
            model_name='nextcloudcollection',
            name='translation_text_length_limit',
            field=models.IntegerField(default=400),
        ),
    ]
