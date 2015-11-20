from django.conf import settings
from elasticsearch import Elasticsearch

es = Elasticsearch(settings.ELASTICSEARCH_URL)

def index(hash, text):
    doc = {
        'text': text,
    }
    resp = es.index(index='hoover', doc_type='doc', id=hash, body=doc)
    assert resp['_id'] == hash


def search(q):
    body = {
        'query': {
            'query_string': {
                'default_field': 'text',
                'query': q,
            }
        },
        'highlight': {'fields': {'text': {}}},
    }
    return es.search(index='hoover', body=body)
