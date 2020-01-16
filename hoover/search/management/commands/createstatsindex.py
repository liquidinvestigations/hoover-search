import requests
import json
from django.core.management.base import BaseCommand
from django.conf import settings

ES_INDEX_PREFIX = ".hoover-snoopstats-"
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

    def handle(self, **kwargs):
        for document_type in ['task', 'blob']:
            index = ES_INDEX_PREFIX + document_type
            url = f'{settings.HOOVER_ELASTICSEARCH_URL}/{index}'

            config = {'mappings': {document_type: ES_MAPPINGS[document_type]}}
            resp = requests.put(
                url,
                data=json.dumps(config),
                headers={'Content-Type': 'application/json'},
            )

            if resp.status_code == 200:
                print(f"Created stats index {index}")
                return
            elif 'resource_already_exists_exception' in resp.text:
                return
            raise RuntimeError(f"Unexpected response {resp!r} {resp.text}")
