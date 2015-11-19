import subprocess
from django.core.management.base import BaseCommand
from ...models import Document
from ... import es
from ...utils import now


class Command(BaseCommand):

    help = "Run an indexing worker"

    def handle(self, verbosity, **options):
        doc = Document.objects.filter(indexed=False).order_by('id').first()

        assert doc.url.startswith('file:///')
        file_path = doc.url[len('file://'):]

        text = subprocess.check_output(['pdftotext', file_path, '-'])

        es.index(doc.hash, text)

        doc.indexed = True
        doc.index_time = now()
        doc.save()
