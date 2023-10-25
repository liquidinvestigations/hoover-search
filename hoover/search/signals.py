import requests
from django.dispatch import Signal
from django.db.models import post_save
from .models import NextcloudCollection
from django.conf import settings
from django.dispatch import receiver

search = Signal(['request', 'collections', 'duration', 'success'])
doc = Signal(['request', 'collection', 'doc_id', 'duration', 'success'])
batch = Signal(['request', 'collections', 'duration', 'success', 'query_count'])
rate_limit_exceeded = Signal(['username'])


@receiver(post_save, sender=NextcloudCollection)
def sync_nextcloud_collections_signal(**kwargs):
    """Signal that calls a snoop endpoint to sync nextcloud collections.

    Whenever a NextcloudCollection object is saved this signal will
    make the call and sync the collections.
    """
    sync_nextcloud_collections()


def sync_nextcloud_collections():
    """Calls a snoop endpoint to sync nextcloud collections.
    """
    nc_collections = [
        {
            'webdav_url': col.url,
            'webdav_username': col.username,
            'webdav_password': col.password,
            'name': col.name,
            'process': True,
            'sync': False,
            'ocr_languages': '',
            'max_result_window': 100000,
            'refresh_interval': '1s',
            'pdf_preview_enabled': False,
            'thumbnail_generator_enabled': False,
            'image_classification_object_detection_enabled': False,
            'image_classification_classify_images_enabled': False,
            'nlp_language_detection_enabled': False,
            'nlp_fallback_language': 'en',
            'nlp_entity_extraction_enabled': False,
            'translation_enabled': False,
            'translation_target_languages': 'en',
            'translation_text_length_limit': 400,
            'default_table_header': '',
            'explode_table_rows': False,
            's3_blobs_address': '',
            's3_blobs_access_key': '',
            's3_blobs_secret_key': '',
        }
        for col in NextcloudCollection.objects.all()
    ]
    url = settings.SNOOP_BASE_URL + '/common/sync_nextcloudcollections'
    resp = requests.post(url, json=nc_collections)
    if not resp.status_code == 200:
        raise RuntimeError(f'Unexpected response: {resp}')
