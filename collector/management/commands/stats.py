from django.core.management.base import BaseCommand
from ...models import Document


class Command(BaseCommand):

    help = "Run an indexing worker"

    def handle(self, verbosity, **options):
        print 'total:', len(Document.objects.all())
        print 'indexed:', len(Document.objects.filter(indexed=True))
        print 'remaining:', len(Document.objects.filter(indexed=False))
