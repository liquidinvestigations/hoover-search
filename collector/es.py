from django.conf import settings
from elasticsearch import Elasticsearch, helpers
from elasticsearch.client.utils import _make_path

es = Elasticsearch(settings.ELASTICSEARCH_URL)
DOCTYPE = 'doc'

def create_index(collection_id, name):
    es.indices.create(index=_index_id(collection_id))
    es.indices.put_alias(index=_index_id(collection_id), name=name)

def _index_id(collection_id):
    return settings.ELASTICSEARCH_INDEX_PREFIX + str(collection_id)

def index(collection_id, doc):
    resp = es.index(
        index=_index_id(collection_id),
        doc_type=DOCTYPE,
        id=doc['id'],
        body=doc,
    )


def exists(collection_id, doc_id):
    path = _make_path(_index_id(collection_id), DOCTYPE, doc_id)
    (status, _) = es.transport.perform_request('HEAD', path, {'ignore': 404})
    return status == 200


def search(query, fields, highlight, collections, from_, size):
    if not collections:
        # if index='', elasticsearch will search in all indices, so we make
        # sure to return an empty result set
        empty_query = {'query': {'bool': {'must_not': {'match_all': {}}}}}
        return es.search(body=empty_query)

    body = {
        'from': from_,
        'size': size,
        'query': query,
        'fields': fields,
    }

    if highlight:
        body['highlight'] = highlight

    return es.search(index=','.join(collections), body=body)


def delete(collection_id):
    es.indices.delete(index=_index_id(collection_id))


def delete_all():
    for index in es.indices.get(index='*'):
        if index.startswith(settings.ELASTICSEARCH_INDEX_PREFIX):
            es.indices.delete(index=index)


def refresh():
    es.indices.refresh()


def count(collection_id):
    return es.count(index=_index_id(collection_id))['count']


def aliases(collection_id):
    name = _index_id(collection_id)
    return set(es.indices.get_aliases(index=name)[name]['aliases'])


def create_alias(collection_id, name):
    es.indices.put_alias(index=_index_id(collection_id), name=name)


def delete_aliases(collection_id):
    es.indices.delete_alias(index=_index_id(collection_id), name='*')


def stats():
    return {
        index: {
            'aliases': list(amap['aliases']),
            'documents': es.count(index=index)['count'],
        }
        for index, amap in es.indices.get_aliases().items()
    }


def list_indices():
    for index in es.indices.get(index='*'):
        if index.startswith(settings.ELASTICSEARCH_INDEX_PREFIX):
            suffix = index[len(settings.ELASTICSEARCH_INDEX_PREFIX):]
            try:
                collection_id = int(suffix)
            except ValueError:
                continue
            yield collection_id
