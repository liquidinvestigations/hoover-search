import logging
from django.db import transaction
from . import es

logger = logging.getLogger(__name__)


class TextMissing(RuntimeError):
    pass


def index(collection, doc):
    data = doc.get_data()
    index_doc = dict(
        data.get('content'),
        _version=data['version'],
    )
    es.index(collection.id, index_doc)
    logger.debug('%s ok', doc.id)


def update_collection(collection):
    logger.info('updating %r', collection)
    queue = collection.get_loader().documents()
    for doc in queue:
        index(collection, doc)
