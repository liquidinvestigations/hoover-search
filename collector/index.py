import logging
from django.db import transaction
from .models import Document
from . import es
from .utils import now, open_url

logger = logging.getLogger(__name__)


def index(doc):
    logger.info('indexing %s', doc)

    with open_url(doc.url) as f:
        text = f.read()

    es.index(doc.slug, {
        'text': text,
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

            index(doc)
