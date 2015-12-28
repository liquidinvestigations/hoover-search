import logging
import threading
import subprocess
from django.db import transaction
from . import es
from .utils import now, threadsafe

logger = logging.getLogger(__name__)


class TextMissing(RuntimeError):
    pass


def documents_to_index(collection):
    indexed = es.get_slugs(collection.slug)

    for doc in collection.get_loader().documents():
        slug = doc.metadata['slug']
        if slug in indexed:
            logger.debug('%s skipped', slug)
            continue

        yield doc


def index(collection, doc):
    data = dict(
        doc.metadata,
        text=doc.text(),
        collection=collection.slug,
    )
    es.index(data)
    logger.debug('%s ok', data['slug'])


def index_from_queue(queue, collection):
    for doc in queue:
        index(collection, doc)


def index_local_file(collection, local_path, slug, url):
    if local_path.endswith('.pdf'):
        text = subprocess.check_output(['pdftotext', local_path, '-'])
        es.index({
            'title': slug,
            'text': text,
            'url': url,
            'slug': slug,
            'collection': collection.slug,
        })

    else:
        raise RuntimeError("Unknown file type %r" % local_path)


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
