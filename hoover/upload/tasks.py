"""Tasks to track user uploads into collections.

These tasks are used to keep track of the processing status of an uploaded file in hoover-snoop.
"""
from ..search import celery as cel
from django.conf import settings
from urllib.parse import quote
import logging
import requests

from hoover.search import models

log = logging.getLogger(__name__)

# TODO correct queue
UPLOAD_KEY = 'hoover.search.upload'


@cel.app.task(bind=True, queue=UPLOAD_KEY, name=UPLOAD_KEY, max_retries=None)
def poll_processing_status(self, *args, **kwargs):
    """Task that polls for the processing status of an uploaded file in snoop.

    First polls, if the file has been already created in snoop. If the file exists
    the tasks polls to get the processing status for that upload and saves it in the database.
    After processing is done it saves the upload as done.

    Args:
        kwargs['collection_name']: The collection name as a string.
        kwargs['directory_pk']: The primary key of the directory in snoop.
        kwargs['upload_pk']: The primary key of the upload that should be monitored..
    """
    try:
        collection_name = kwargs.get('collection_name')
        filename = kwargs.get('filename')
        # first check if file exists in snoop database and retrieve it's blobs primary key.
        blob_pk = file_exists(collection_name,
                              kwargs.get('directory_pk'),
                              filename,
                              )
        if not blob_pk:
            # raise RuntimeError(f'{filename} does not exist in snoop in collection: {collection_name}')
            raise self.retry(countdown=10)

        upload = models.Upload.objects.get(pk=kwargs.get('upload_pk'))

        # if file exists, check processing status for it's corresponding blob
        status = processing_status(collection_name, blob_pk)
        if not status['finished']:
            upload.snoop_tasks_done = status['done_count']
            upload.snoop_tasks_total = status['total_count']
            upload.save()
            raise self.retry(countdown=10)
            # raise RuntimeError(f'{blob_pk} in collection: {collection_name} not processed.')

        upload.snoop_tasks_done = status['done_count']
        upload.snoop_tasks_total = status['total_count']
        upload.processed = True
        upload.save()
        return True

    except Exception as e:
        log.error('poll_processing_status celery task execution failed!')
        log.exception(e)
        raise


def file_exists(collection_name, directory_pk, filename):
    """Checks a snoop endpoint for the existence of a file.

    Calls the endpoint and returns the blobs primary key if the file exists.

    Args:
        collection_name: The collection name as a string.
        directory_pk: The primary key of the directory in snoop (string or int).
        filename: The original filename of the uploaded file as a string.

    Returns:
        The primary key of the corresponding blob, if the file exists or None if the file
        doesn't exist.
    """
    filename_encoded = quote(filename)
    url = settings.SNOOP_BASE_URL + f'/collections/{collection_name}/{directory_pk}/{filename_encoded}/exists'
    resp = requests.get(url)

    if not resp.status_code == 200:
        log.info(f'File "{filename}" not yet found in snoop database!')
        return False

    log.info(f'File "{filename}" found in snoop database!')
    blob_pk = resp.content.decode()

    return blob_pk


def processing_status(collection_name, blob_pk):
    """Calls a snoop endpoint to check the processing status of a given blob.

    Args:
        collection_name: The collection name as a string.
        blob_pk: The primary key (hash) of the blob in snoop.

    Returns:
        A json that looks like this: {'finished': False, 'done_count': 0, 'total_count': 0}
    """
    url = settings.SNOOP_BASE_URL + f'/collections/{collection_name}/{blob_pk}/processing_status'

    resp = requests.get(url)
    if not resp.status_code == 200:
        log.error(f'Error while fetching processing status for blob: {blob_pk}!')
        return None

    res = resp.json()

    log.info(f'Processing for blob: {blob_pk} fetched! Status: {res["finished"]}')

    return resp.json()
