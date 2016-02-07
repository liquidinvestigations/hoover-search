from django.conf import settings
from elasticsearch import Elasticsearch, helpers
from elasticsearch.client.utils import _make_path

es = Elasticsearch(settings.ELASTICSEARCH_URL)
DOCTYPE = 'doc'
INDEX = 'hoover'

def index(doc):
    id = doc['collection'] + '/' + doc['slug']
    resp = es.index(id=id, index=INDEX, doc_type=DOCTYPE, body=doc)


def exists(collection, slug):
    path = _make_path(INDEX, DOCTYPE, '%s/%s' % (collection, slug))
    (status, _) = es.transport.perform_request('HEAD', path, {'ignore': 404})
    return status == 200


def search(query, fields, highlight, collections, from_, size):
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
        'from': from_,
        'size': size,
        'query': {
            'filtered': {
                'filter': filter,
                'query': query,
            },
        },
        'fields': fields,
    }

    if highlight:
        body['highlight'] = highlight

    return es.search(index=INDEX, body=body)


def delete(collection):
    docs = (
        r['_id'] for r in
        helpers.scan(es, {
            'query': {'term': {'collection': collection}},
            'fields': ['_id'],
        })
    )
    actions = [
        {'_op_type': 'delete', '_index': INDEX, '_type': DOCTYPE, '_id': d}
        for d in docs
    ]
    helpers.bulk(es, actions)


def flush():
    es.indices.delete(index=INDEX, ignore=[400, 404])


def refresh():
    es.indices.refresh(index=INDEX)


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
    res = es.search(index=INDEX, search_type='count', body=body)
    return {
        bucket['key']: bucket['doc_count']
        for bucket in res['aggregations']['collections']['buckets']
    }
