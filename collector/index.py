import logging
import subprocess
import urllib
from contextlib import contextmanager
from django.db import transaction
from .models import Document
from . import es
from .utils import now

logger = logging.getLogger(__name__)


@contextmanager
def open_url(doc):
    f = urllib.urlopen(doc.url)
    try:
        yield f
    finally:
        f.close()


def index(doc):
    logger.info('indexing %s', doc)

    with open_url(doc) as f:
        text = subprocess.check_output(['pdftotext', '-', '-'], stdin=f)

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
