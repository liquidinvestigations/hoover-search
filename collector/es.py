from django.conf import settings
from elasticsearch import Elasticsearch, helpers
from elasticsearch.client.utils import _make_path
from elasticsearch.exceptions import NotFoundError, TransportError

es = Elasticsearch(settings.ELASTICSEARCH_URL)
DOCTYPE = 'doc'

def create_index(collection_id, name):
    es.indices.create(index=_index_name(collection_id))

def _index_name(collection_id):
    from .models import Collection
    return Collection.objects.get(id=collection_id).index

def _index_id(index):
    from .models import Collection
    return Collection.objects.get(index=index).id

def index(collection_id, doc):
    resp = es.index(
        index=_index_name(collection_id),
        doc_type=DOCTYPE,
        id=doc['id'],
        body=doc,
    )


def exists(collection_id, doc_id):
    path = _make_path(_index_name(collection_id), DOCTYPE, doc_id)
    (status, _) = es.transport.perform_request('HEAD', path, {'ignore': 404})
    return status == 200


def get(collection_id, doc_id):
    return es.get(
        index=_index_name(collection_id),
        doc_type=DOCTYPE,
        id=doc_id,
    )


def search(query, fields, highlight, collections, from_, size):
    from .models import Collection
    indices = ','.join(
        c.index for c in
        Collection.objects.filter(name__in=collections)
    )

    if not indices:
        # if index='', elasticsearch will search in all indices, so we make
        # sure to return an empty result set
        empty_query = {'query': {'bool': {'must_not': {'match_all': {}}}}}
        return (es.search(body=empty_query), {})

    body = {
        'from': from_,
        'size': size,
        'query': query,
        'fields': fields,
        'aggs': {
            'count_by_index': {
                'terms': {
                    'field': '_index',
                },
            },
        },
    }

    if highlight:
        body['highlight'] = highlight

    rv = es.search(
        index=indices,
        ignore_unavailable=True,
        body=body,
    )

    count_by_index = {
        _index_id(b['key']): b['doc_count']
        for b in rv['aggregations']['count_by_index']['buckets']
    }
    return (rv, count_by_index)


def delete_index(collection_id, ok_missing=False):
    es.indices.delete(
        index=_index_name(collection_id),
        ignore=[404] if ok_missing else [],
    )


def delete_all():
    for index in es.indices.get(index='*'):
        if index.startswith(settings.ELASTICSEARCH_INDEX_PREFIX):
            es.indices.delete(index=index)


def refresh():
    es.indices.refresh()


def count(collection_id):
    try:
        return es.count(index=_index_name(collection_id))['count']
    except NotFoundError:
        return None


def aliases(collection_id):
    name = _index_name(collection_id)
    alias_map = es.indices.get_aliases(index=name)
    return set(alias_map.get(name, {}).get('aliases', {}))


def create_alias(collection_id, name):
    try:
        es.indices.put_alias(index=_index_name(collection_id), name=name)
    except NotFoundError:
        es.indices.create(index=_index_name(collection_id))
        es.indices.put_alias(index=_index_name(collection_id), name=name)


def delete_aliases(collection_id):
    es.indices.delete_alias(index=_index_name(collection_id), name='*')


def set_mapping(collection_id, properties):
    es.indices.put_mapping(
        index=_index_name(collection_id),
        doc_type=DOCTYPE,
        body={'properties': properties},
    )


def status():
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
