from django.conf import settings
from elasticsearch import Elasticsearch, helpers

es = Elasticsearch(settings.ELASTICSEARCH_URL)

def index(doc):
    resp = es.index(index='hoover', doc_type='doc', body=doc)


def search(q, collections):
    if collections:
        filter = {
            'or': [
                {'term': {'collection': col}}
                for col in collections
            ],
        }

    else:
        filter = {'bool': {'must_not': {'match_all': {}}}}

    body = {
        'query': {
            'filtered': {

                'filter': filter,

                'query': {
                    'query_string': {
                        'default_field': 'text',
                        'query': q,
                    }
                },

            },
        },

        'fields': ['title', 'url'],

        'highlight': {'fields': {'text': {}}},
    }
    return es.search(index='hoover', body=body)


def get_slugs(collection):
    return set(
        r['fields']['slug'][0]
        for r in
        helpers.scan(es, {
            'query': {'term': {'collection': collection}},
            'fields': ['slug'],
        })
    )


def flush():
    es.indices.delete(index='hoover', ignore=[400, 404])


def stats():
    body = {
        'aggregations': {
            'collections': {
                'terms': {
                    'field': 'collection',
                },
            },
        },
    }
    res = es.search(index='hoover', search_type='count', body=body)
    return {
        bucket['key']: bucket['doc_count']
        for bucket in res['aggregations']['collections']['buckets']
    }
