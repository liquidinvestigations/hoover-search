import sys
from django.core.management.base import BaseCommand
from django.conf import settings
from ... import models
from ...es import elasticsearch

MAPPINGS = {
    "doc": {
        "properties": {
            "id": {"type": "string", "index": "not_analyzed"},
            "path": {"type": "string", "index": "not_analyzed"},
            "suffix": {"type": "string", "index": "not_analyzed"},
            "md5": {"type": "string", "index": "not_analyzed"},
            "sha1": {"type": "string", "index": "not_analyzed"},
            "filetype": {"type": "string", "index": "not_analyzed"},
            "lang": {"type": "string", "index": "not_analyzed"},
            "date": {"type": "date", "index": "not_analyzed"},
            "date-created": {"type": "date", "index": "not_analyzed"},
            "attachments": {"type": "boolean"},
            "message-id": {"type": "string", "index": "not_analyzed"},
            "in-reply-to": {"type": "string", "index": "not_analyzed"},
            "thread-index": {"type": "string", "index": "not_analyzed"},
            "references": {"type": "string", "index": "not_analyzed"},
            "message": {"type": "string", "index": "not_analyzed"},
            "word-count": {"type": "integer"},
            "rev": {"type": "integer"},
            "content-type": {"type": "string", "index": "not_analyzed"},
            "size": {"type": "integer"},
        }
    }
}

SETTINGS = {
    "analysis": {
        "analyzer": {
            "default": {
                "tokenizer": "standard",
                "filter": ["standard", "lowercase", "asciifolding"],
            }
        }
    }
}


class Command(BaseCommand):
    help = "Reset the elasticsearch index"

    def add_arguments(self, parser):
        parser.add_argument('name')

    def handle(self, name, **options):
        try:
            collection = models.Collection.objects.get(name=name)
        except models.Collection.DoesNotExist:
            print(f"Collection {name} does not exist")
            sys.exit(1)

        with elasticsearch() as es:
            es.indices.delete(collection.index, ignore=[400, 404])
            es.indices.create(collection.index, {
                "mappings": MAPPINGS,
                "settings": SETTINGS,
            })
