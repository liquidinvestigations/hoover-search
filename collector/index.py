import logging
import threading
import subprocess
from django.db import transaction
from . import es
from .utils import now, threadsafe

logger = logging.getLogger(__name__)


class TextMissing(RuntimeError):
    pass


def index(collection, doc):
    data = dict(
        doc.metadata,
        text=doc.text(),
        collection=collection.slug,
    )
    es.index(collection.id, data)
    logger.debug('%s ok', data['slug'])


def index_from_queue(queue, collection):
    for doc in queue:
        doc_slug = doc.metadata['slug']
        if es.exists(collection.id, doc_slug):
            logger.debug('%s skipped', doc_slug)
            continue
        index(collection, doc)


def index_local_file(collection, local_path, slug, url):
    if local_path.endswith('.pdf'):
        text = subprocess.check_output(['pdftotext', local_path, '-'])
        es.index(collection.id, {
            'title': slug,
            'text': text.decode('utf-8'),
            'url': url,
            'slug': slug,
            'collection': collection.slug,
        })

    else:
        raise RuntimeError("Unknown file type %r" % local_path)


def update_collection(collection, threads=1):
    logger.info('updating %r', collection)
    queue = threadsafe(collection.get_loader().documents())

    thread_list = [
        threading.Thread(target=index_from_queue, args=(queue, collection))
        for _ in range(threads)
    ]

    for thread in thread_list:
        thread.start()

    for thread in thread_list:
        thread.join()
