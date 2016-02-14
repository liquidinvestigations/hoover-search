import logging
import threading
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
        collection=collection.name,
    )
    es.index(collection.id, data)
    logger.debug('%s ok', data['id'])


def index_from_queue(queue, collection):
    for doc in queue:
        doc_slug = doc.metadata['id']
        if es.exists(collection.id, doc_slug):
            logger.debug('%s skipped', doc_slug)
            continue
        index(collection, doc)


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
