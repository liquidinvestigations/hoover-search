# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


def create_collection(apps, schema_editor):
    Collection = apps.get_model('collector', 'Collection')
    Document = apps.get_model('collector', 'Document')
    if len(Document.objects.all()) == 0:
        return
    col = Collection.objects.create(slug='mof')
    for doc in Document.objects.all():
        doc.collection = col
        doc.save()


class Migration(migrations.Migration):

    dependencies = [
        ('collector', '0002_document_text_url'),
    ]

    operations = [
        migrations.CreateModel(
            name='Collection',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('slug', models.CharField(unique=True, max_length=256)),
                ('title', models.CharField(max_length=2048, blank=True)),
            ],
        ),
        migrations.AddField(
            model_name='document',
            name='collection',
            field=models.ForeignKey(to='collector.Collection', null=True),
        ),
        migrations.RunPython(create_collection),
        migrations.AlterField(
            model_name='document',
            name='collection',
            field=models.ForeignKey(to='collector.Collection'),
        ),
    ]
