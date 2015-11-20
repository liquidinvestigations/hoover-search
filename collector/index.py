import logging
from django.db import transaction
import requests
from .models import Document
from . import es
from .utils import now

logger = logging.getLogger(__name__)


class TextMissing(RuntimeError):
    pass


def index(doc):
    logger.info('indexing %s', doc)

    resp = requests.get(doc.text_url)
    if resp.status_code == 404:
        raise TextMissing(str(doc))

    if resp.status_code != 200:
        raise RuntimeError("failed to get text for %s: %r" % (doc, resp))

    es.index('mof/' + doc.slug, {
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
