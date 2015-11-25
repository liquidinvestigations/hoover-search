import logging
import json
from django.db import transaction
from django.utils.module_loading import import_string
import requests
from .models import Document
from . import es
from .utils import now

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


def update_collection(collection):
    logger.info('updating %r', collection)
    for doc in documents_to_index(collection):
        resp = requests.get(doc['text_url'])
        if resp.status_code == 404:
            raise TextMissing(doc['slug'])

        if resp.status_code != 200:
            msg = "failed to get text %s: %r" % (doc['slug'], resp)
            raise RuntimeError(msg)

        doc_id = collection.slug + '/' + doc['slug']
        doc['collection'] = collection.slug
        doc['text'] = resp.text
        es.index(doc_id, doc)
        logger.debug('%s ok', doc['slug'])


def index(doc):
    logger.info('indexing %s', doc)
    collection = doc.collection

    resp = requests.get(doc.text_url)
    if resp.status_code == 404:
        raise TextMissing(str(doc))

    if resp.status_code != 200:
        raise RuntimeError("failed to get text for %s: %r" % (doc, resp))

    es.index(collection.slug + '/' + doc.slug, {
        'collection': collection.slug,
        'slug': doc.slug,
        'text': resp.text,
        'title': doc.title,
        'url': doc.url,
    })

    doc.indexed = True
    doc.index_time = now()
    doc.save()


def work_loop():
    while True:
        with transaction.atomic():
            doc = (
                Document.objects
                .select_for_update()
                .filter(indexed=False)
                .order_by('?')
                .first()
            )

            if doc is None:
                return

            try:
                index(doc)
            except TextMissing:
                logger.warn('text missing for document %s', doc)
