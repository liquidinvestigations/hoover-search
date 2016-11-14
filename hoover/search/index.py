import logging
from django.db import transaction
from . import es

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


def update_collection(collection):
    logger.info('updating %r', collection)
    queue = collection.get_loader().documents()
    for doc in queue:
        index(collection, doc)
