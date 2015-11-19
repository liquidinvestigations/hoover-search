import subprocess
from django.core.management.base import BaseCommand
from ...models import Document


class Command(BaseCommand):

    help = "Run an indexing worker"

    def handle(self, verbosity, **options):
        doc = Document.objects.filter(indexed=False).order_by('id').first()
        assert doc.url.startswith('file:///')
        file_path = doc.url[len('file://'):]
        text = subprocess.check_output(['pdftotext', file_path, '-'])
        print repr(text)
