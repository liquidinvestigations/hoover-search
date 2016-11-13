import json
from contextlib import contextmanager
from django.conf import settings
from elasticsearch import Elasticsearch
from elasticsearch.client.utils import _make_path
from elasticsearch.exceptions import NotFoundError, RequestError, ConnectionError

DOCTYPE = 'doc'

class SearchError(Exception):
    def __init__(self, reason):
        self.reason = reason

@contextmanager
def elasticsearch():
    try:
        yield Elasticsearch(settings.HOOVER_ELASTICSEARCH_URL)
    except ConnectionError:
        raise SearchError('Could not connect to Elasticsearch.')
    except RequestError as e:
        reason = 'reason unknown'
        try:
            if e.info:
                reason = e.info['error']['root_cause'][0]['reason']
        except LookupError:
            pass
        raise SearchError('Elasticsearch failed: ' + reason)

def create_index(collection_id, name):
    with elasticsearch() as es:
        es.indices.create(index=_index_name(collection_id))

def _index_name(collection_id):
    from .models import Collection
    return Collection.objects.get(id=collection_id).index

def _index_id(index):
    from .models import Collection
    return Collection.objects.get(index=index).id

def index(collection_id, doc):
    with elasticsearch() as es:
        resp = es.index(
            index=_index_name(collection_id),
            doc_type=DOCTYPE,
            id=doc['id'],
            body=doc,
        )


def exists(collection_id, doc_id):
    path = _make_path(_index_name(collection_id), DOCTYPE, doc_id)
    with elasticsearch() as es:
        (status, _) = es.transport.perform_request('HEAD', path, {'ignore': 404})
        return status == 200


def get(collection_id, doc_id):
    with elasticsearch() as es:
        return es.get(
            index=_index_name(collection_id),
            doc_type=DOCTYPE,
            id=doc_id,
        )

def _get_indices(collections):
    from .models import Collection
    indices = ','.join(
        c.index for c in
        Collection.objects.filter(name__in=collections)
    )
    return indices

def batch_count(query_strings, collections, aggs=None):
    def _build_query_lines(query_string, meta={}, aggs=None):
        query_body = {
            "query": {
                "query_string": {
                    "query": query_string,
                }
            }
        }
        if aggs:
            query_body['aggs'] = aggs
        return json.dumps(meta) + "\n" + json.dumps(query_body) + "\n"

    indices = _get_indices(collections)

    body = "".join(
        _build_query_lines(q, {}, aggs)
        for q in query_strings
    )

    with elasticsearch() as es:
        rv = es.msearch(
            index=indices,
            body=body,
            doc_type=DOCTYPE,
            search_type='count'
        )

    for query_string, response in zip(query_strings, rv.get('responses', [])):
        response['_query_string'] = query_string

    return rv

def search(query, fields, highlight, collections, from_, size, sort, aggs):
    indices = _get_indices(collections)

    if not indices:
        # if index='', elasticsearch will search in all indices, so we make
        # sure to return an empty result set
        empty_query = {'query': {'bool': {'must_not': {'match_all': {}}}}}
        with elasticsearch() as es:
            return (es.search(body=empty_query), {})

    body = {
        'from': from_,
        'size': size,
        'query': query,
        'fields': fields,
        'sort': sort,
        'aggs': dict(aggs, **{
            'count_by_index': {
                'terms': {
                    'field': '_index',
                },
            },
        }),
    }

    if highlight:
        body['highlight'] = highlight

    with elasticsearch() as es:
        rv = es.search(
            index=indices,
            ignore_unavailable=True,
            body=body,
            request_timeout=60,
        )

    count_by_index = {
        _index_id(b['key']): b['doc_count']
        for b in rv['aggregations']['count_by_index']['buckets']
    }
    return (rv, count_by_index)


def delete_index(collection_id, ok_missing=False):
    with elasticsearch() as es:
        es.indices.delete(
            index=_index_name(collection_id),
            ignore=[404] if ok_missing else [],
        )


def delete_all():
    with elasticsearch() as es:
        for index in es.indices.get(index='*'):
            if index.startswith(settings.ELASTICSEARCH_INDEX_PREFIX):
                es.indices.delete(index=index)


def refresh():
    with elasticsearch() as es:
        es.indices.refresh()


def count(collection_id):
    es = Elasticsearch(settings.HOOVER_ELASTICSEARCH_URL)
    try:
        return es.count(index=_index_name(collection_id))['count']
    except NotFoundError:
        return None


def aliases(collection_id):
    with elasticsearch() as es:
        name = _index_name(collection_id)
        alias_map = es.indices.get_aliases(index=name)
        return set(alias_map.get(name, {}).get('aliases', {}))


def create_alias(collection_id, name):
    index = _index_name(collection_id)
    with elasticsearch() as es:
        try:
            es.indices.put_alias(index=index, name=name)
        except NotFoundError:
            es.indices.create(index=index)
            es.indices.put_alias(index=index, name=name)


def delete_aliases(collection_id):
    with elasticsearch() as es:
        es.indices.delete_alias(index=_index_name(collection_id), name='*')


def set_mapping(collection_id, properties):
    with elasticsearch() as es:
        es.indices.put_mapping(
            index=_index_name(collection_id),
            doc_type=DOCTYPE,
            body={'properties': properties},
        )


def status():
    with elasticsearch() as es:
        return {
            index: {
                'aliases': list(amap['aliases']),
                'documents': es.count(index=index)['count'],
            }
            for index, amap in es.indices.get_aliases().items()
        }


def list_indices():
    with elasticsearch() as es:
        for index in es.indices.get(index='*'):
            if index.startswith(settings.ELASTICSEARCH_INDEX_PREFIX):
                suffix = index[len(settings.ELASTICSEARCH_INDEX_PREFIX):]
                try:
                    collection_id = int(suffix)
                except ValueError:
                    continue
                yield collection_id
