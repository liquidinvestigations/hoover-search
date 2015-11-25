import logging
import json
import threading
from django.db import transaction
from django.utils.module_loading import import_string
import requests
from . import es
from .utils import now, threadsafe

logger = logging.getLogger(__name__)


class TextMissing(RuntimeError):
    pass


def documents_to_index(collection):
    loader_cls = import_string(collection.loader)
    loader = loader_cls(**json.loads(collection.options))

    indexed = es.get_slugs(collection.slug)

    for doc in loader.documents():
        if doc['slug'] in indexed:
            logger.debug('%s skipped', doc['slug'])
            continue

        yield doc


def index_from_queue(queue, collection):
    for doc in queue:
        resp = requests.get(doc['text_url'])
        if resp.status_code == 404:
            raise TextMissing(doc['slug'])

        if resp.status_code != 200:
            msg = "failed to get text %s: %r" % (doc['slug'], resp)
            raise RuntimeError(msg)

        doc['collection'] = collection.slug
        doc['text'] = resp.text
        es.index(doc)
        logger.debug('%s ok', doc['slug'])


def update_collection(collection, threads=1):
    logger.info('updating %r', collection)
    queue = threadsafe(documents_to_index(collection))

    thread_list = [
        threading.Thread(target=index_from_queue, args=(queue, collection))
        for _ in range(threads)
    ]

    for thread in thread_list:
        thread.start()

    for thread in thread_list:
        thread.join()
