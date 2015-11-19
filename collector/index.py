import subprocess
from django.db import transaction
from .models import Document
from . import es
from .utils import now


def index(doc):
    assert doc.url.startswith('file:///')
    file_path = doc.url[len('file://'):]

    text = subprocess.check_output(['pdftotext', file_path, '-'])

    es.index(doc.hash, text)

    doc.indexed = True
    doc.index_time = now()
    doc.save()


def work():
    with transaction.atomic():
        doc = (
            Document.objects
            .select_for_update()
            .filter(indexed=False)
            .order_by('id')
            .first()
        )
        index(doc)
