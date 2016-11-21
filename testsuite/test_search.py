import json
import pytest
from django.conf import settings
from elasticsearch import Elasticsearch
from hoover.search import models, index, signals
from .fixtures import skip_twofactor, listen

pytestmark = pytest.mark.django_db
es = Elasticsearch(settings.HOOVER_ELASTICSEARCH_URL)

class MockDoc:

    def __init__(self, id, data):
        self.id = id
        self.metadata = dict(data, id=id)

    def text(self):
        return self.metadata.get('text')

@pytest.yield_fixture
def finally_cleanup_index():
    id_list = []
    try:
        yield id_list.append
    finally:
        for id in id_list:
            es.indices.delete(id, ignore=[404])

@pytest.fixture
def api(client, skip_twofactor):
    class Api:
        @staticmethod
        def collections():
            res = client.get('/collections')
            return res.json()

        @staticmethod
        def search(query, collections):
            data = {'query': query, 'collections': collections}
            res = client.post('/search',
                data=json.dumps(data).encode('utf-8'),
                content_type='application/json',
            )
            return res.json()

        @staticmethod
        def doc(collection, id):
            return client.get('/doc/{}/{}'.format(collection, id))

        @staticmethod
        def batch(query_strings, collections):
            data = {
                "query_strings": query_strings,
                "collections": collections,
            }
            res = client.post(
                '/batch',
                data=json.dumps(data).encode('utf-8'),
                content_type='application/json',
            )
            return res.json()

    return Api

class Response:
    def __init__(self, **kwargs):
        for k, v in dict({'status_code': 200}, **kwargs).items():
            setattr(self, k, v)

@pytest.fixture
def external(monkeypatch):
    class mock_requests:
        @staticmethod
        def get(url):
            return urlmap.get(url) or Response(status_code=404)

    urlmap = {}
    monkeypatch.setattr('hoover.search.loaders.external.requests',
        mock_requests)
    return urlmap

def test_all_the_things(finally_cleanup_index, listen, api):
    from hoover.search.es import _index_name, DOCTYPE
    search_events = listen(signals.search)
    col = models.Collection.objects.create(
        name='testcol', index='hoover-testcol', public=True)

    assert {c['name'] for c in api.collections()} == {'testcol'}

    finally_cleanup_index(_index_name(col.id))
    doc = MockDoc('mock1', {'foo': "bar"})
    index.index(col, doc)
    es_index_id = _index_name(col.id)
    data = es.get(index=es_index_id, doc_type=DOCTYPE, id='mock1')
    assert data['_id'] == 'mock1'
    assert data['_source'] == dict(
        id='mock1',
        foo='bar',
        collection='testcol',
        text=None,
    )

    es.indices.refresh()
    hits = api.search({'match_all': {}}, ['testcol'])['hits']['hits']
    assert {hit['_id'] for hit in hits} == {'mock1'}
    assert hits[0]['_collection'] == 'testcol'
    assert hits[0]['_url'] == 'http://testserver/doc/testcol/mock1'

    assert len(search_events) == 1
    assert search_events[0]['collections'] == {col}
    assert search_events[0]['success']

    batch_results = api.batch(["*", "mock1"], ['testcol'])
    assert len(batch_results['responses']) == 2
    assert batch_results['responses'][0]['_query_string'] == "*"
    assert batch_results['responses'][1]['_query_string'] == "mock1"
    assert batch_results['responses'][0]['hits']['total'] == 1
    assert batch_results['responses'][1]['hits']['total'] == 1

def test_external_loader(finally_cleanup_index, listen, api, external):
    from hoover.search.es import _index_name, DOCTYPE
    doc_events = listen(signals.doc)
    col = models.Collection.objects.create(
        name='testcol',
        index='hoover-testcol',
        public=True,
        loader='hoover.search.loaders.external.Loader',
        options='{"documents": "https://example.com/doc/"}',
    )

    external['https://example.com/doc/mock1'] = Response(
        headers={'Content-Type': 'text/plain'},
        content=b"hello world",
    )

    res = api.doc('testcol', 'mock1')
    assert res.status_code == 200
    assert res.content == b'hello world'

    assert len(doc_events) == 1
    assert doc_events[0]['collection'] == col
    assert doc_events[0]['doc_id'] == 'mock1'
    assert doc_events[0]['success']
