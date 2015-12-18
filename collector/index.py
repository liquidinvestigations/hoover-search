import logging
import threading
import subprocess
from django.db import transaction
import requests
from . import es
from .utils import now, threadsafe

logger = logging.getLogger(__name__)


class TextMissing(RuntimeError):
    pass


def documents_to_index(collection):
    indexed = es.get_slugs(collection.slug)

    for doc in collection.get_loader().documents():
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


def index_local_file(collection, local_path, slug, url):
    text = subprocess.check_output([
        'unoconv',
        '-f', 'text',
        '--stdout',
        local_path,
    ])
    es.index({
        'title': slug,
        'text': text,
        'url': url,
        'slug': slug,
        'collection': collection.slug,
    })


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
