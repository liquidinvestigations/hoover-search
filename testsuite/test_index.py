import json
import pytest
from django.conf import settings
from elasticsearch import Elasticsearch
from collector import models, index

pytestmark = pytest.mark.django_db
es = Elasticsearch(settings.ELASTICSEARCH_URL)

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
def api(client):
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
    monkeypatch.setattr('collector.loaders.external.requests', mock_requests)
    return urlmap

def test_all_the_things(finally_cleanup_index, api):
    from collector.es import _index_name, DOCTYPE
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

def test_external_loader(finally_cleanup_index, api, external):
    from collector.es import _index_name, DOCTYPE
    col = models.Collection.objects.create(
        name='testcol',
        index='hoover-testcol',
        public=True,
        loader='collector.loaders.external.Loader',
        options='{"documents": "https://example.com/doc/"}',
    )

    external['https://example.com/doc/mock1'] = Response(
        headers={'Content-Type': 'text/plain'},
        content=b"hello world",
    )

    finally_cleanup_index(_index_name(col.id))
    doc = MockDoc('mock1', {'foo': "bar"})
    index.index(col, doc)
    es.indices.refresh()

    res = api.doc('testcol', 'mock1')
    assert res.status_code == 200
    assert res.content == b'hello world'
