import requests
import json
from django.core.management.base import BaseCommand
from django.conf import settings

ES_INDEX_PREFIX = "_snoopstats-"
ES_MAPPINGS = {
    'task': {
        'properties': {
            'collection': {'type': 'keyword'},
            'func': {'type': 'keyword'},
            'args': {'type': 'keyword'},
            'status': {'type': 'keyword'},
            'date_created': {'type': 'date', 'format': 'date_time'},
            'date_modified': {'type': 'date', 'format': 'date_time'},
            'date_started': {'type': 'date', 'format': 'date_time'},
            'date_finished': {'type': 'date', 'format': 'date_time'},
            'duration': {'type': 'float'},
        },
    },
    'blob': {
        'properties': {
            'collection': {'type': 'keyword'},
            'mime_type': {'type': 'keyword'},
            'mime_encoding': {'type': 'keyword'},
            'date_created': {'type': 'date', 'format': 'date_time'},
            'date_modified': {'type': 'date', 'format': 'date_time'},
        },
    },
}

class Command(BaseCommand):

    help = "Set mappings for the stats indexes"

    def handle(self, name, url, index, public, **kwargs):
        for document_type in ['task', 'blob']:
            index = ES_INDEX_PREFIX + document_type
            url = f'{settings.HOOVER_ELASTICSEARCH_URL}/{index}'

            config = {'mappings': {document_type: ES_MAPPINGS[document_type]}}
            put_resp = requests.put(
                url,
                data=json.dumps(config),
                headers={'Content-Type': 'application/json'},
            )
            print('%s Elasticsearch PUT: %r', document_type, put_resp)
            print('%s Elasticsearch PUT: %r', document_type, put_resp.text)
