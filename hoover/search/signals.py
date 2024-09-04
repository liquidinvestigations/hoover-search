import requests
from django.dispatch import Signal
from django.db.models.signals import post_save, post_delete
from .models import NextcloudCollection, Collection
from django.conf import settings
from django.dispatch import receiver

search = Signal(['request', 'collections', 'duration', 'success'])
doc = Signal(['request', 'collection', 'doc_id', 'duration', 'success'])
batch = Signal(['request', 'collections', 'duration', 'success', 'query_count'])
rate_limit_exceeded = Signal(['username'])


@receiver(post_save, sender=NextcloudCollection)
def sync_nextcloud_collections_signal(sender, instance, **kwargs):
    """Signal that calls a snoop endpoint to sync nextcloud collections.

    Whenever a NextcloudCollection object is saved this signal will
    make the call and sync the collections. Also creates a new Collection with the
    same name.
    """
    sync_nextcloud_collections()
    Collection.objects.update_or_create(
        name=instance.name.lower().replace(' ', '-'),
        defaults=dict(
            index=instance.name.lower().replace(' ', '-'),
        )
    )


@receiver(post_delete, sender=NextcloudCollection)
def delete_collection(sender, instance, **kwargs):
    """Signal that deletes a Collection that corresponds to the nextcloud collection."""
    instance.collection.delete()


def sync_nextcloud_collections():
    """Calls a snoop endpoint to sync nextcloud collections.
    """
    nc_collections = [
        {
            'webdav_url': col.url,
            'webdav_username': col.username,
            'webdav_password': col.password,
            'name': col.name.lower().replace(' ', '-'),
            'process': col.process,
            'sync': col.sync,
            'ocr_languages': col.ocr_languages,
            'max_result_window': col.max_result_window,
            'refresh_interval': '1s',
            'pdf_preview_enabled': col.pdf_preview_enabled,
            'thumbnail_generator_enabled': col.thumbnail_generator_enabled,
            'image_classification_object_detection_enabled': col.image_classification_object_detection_enabled,
            'image_classification_classify_images_enabled': col.image_classification_classify_images_enabled,
            'nlp_language_detection_enabled': col.nlp_language_detection_enabled,
            'nlp_fallback_language': col.nlp_fallback_language,
            'nlp_entity_extraction_enabled': col.nlp_entity_extraction_enabled,
            'translation_enabled': col.translation_enabled,
            'translation_target_languages': col.translation_target_languages,
            'translation_text_length_limit': col.translation_text_length_limit,
            'default_table_header': col.default_table_header,
            'explode_table_rows': col.explode_table_rows,
            's3_blobs_address': col.s3_blobs_address,
            's3_blobs_access_key': col.s3_blobs_access_key,
            's3_blobs_secret_key': col.s3_blobs_secret_key,
        }
        for col in NextcloudCollection.objects.all()
    ]
    url = settings.SNOOP_BASE_URL + '/common/sync_nextcloudcollections'
    resp = requests.post(url, json=nc_collections)
    if not resp.status_code == 200:
        raise RuntimeError(f'Unexpected response: {resp}')
