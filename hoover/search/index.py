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
    for doc, version in queue:
        es_versions = es.versions(collection.id, [doc.id])
        if doc.id in es_versions and es_versions[doc.id] == version:
            continue
        index(collection, doc)
