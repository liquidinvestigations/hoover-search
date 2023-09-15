import time
import json
import pytest
from django.conf import settings
from elasticsearch import Elasticsearch
from hoover.search import models, signals
from .fixtures import listen

from django.contrib.auth import get_user_model

import responses

pytestmark = pytest.mark.django_db
es = Elasticsearch(settings.HOOVER_ELASTICSEARCH_URL)


class MockDoc:

    def __init__(self, id, data):
        self.id = id
        self.metadata = dict(data, id=id)

    def text(self):
        return self.metadata.get('text')

    def get_data(self):
        return self.metadata


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
            res = client.get('/api/v1/collections')
            return res.json()

        @staticmethod
        def search(query, collections, user, refresh=False):
            data = {'query': query, 'collections': collections}
            client.force_login(user)
            url = '/api/v1/search'
            if refresh:
                url += '?refresh=t'
            res = client.post(url,
                              data=json.dumps(data).encode('utf-8'),
                              content_type='application/json',
                              )
            client.logout()
            return res.json()

        @staticmethod
        def async_search(query, collections, user, refresh=False):
            data = {'query': query, 'collections': collections}
            client.force_login(user)
            url = '/api/v1/async_search'
            if refresh:
                url += '?refresh=t'
            res = client.post(url,
                              data=json.dumps(data).encode('utf-8'),
                              content_type='application/json',
                              )
            client.logout()
            return res.json()

        @staticmethod
        def async_search_get(sid, user, wait=False):
            client.force_login(user)
            url = '/api/v1/async_search/' + sid
            if wait:
                url += '?wait=t'
            res = client.get(url)
            client.logout()
            return res.json()

        @staticmethod
        def doc(collection, id):
            return client.get('/api/v1/doc/{}/{}'.format(collection, id))

        @staticmethod
        def batch(query_strings, collections):
            data = {
                "query_strings": query_strings,
                "collections": collections,
            }
            res = client.post(
                '/api/v1/batch',
                data=json.dumps(data).encode('utf-8'),
                content_type='application/json',
            )
            return res.json()

    return Api


class Response:
    def __init__(self, **kwargs):
        for k, v in dict({'status_code': 200}, **kwargs).items():
            setattr(self, k, v)


class JsonResponse(Response):
    def __init__(self, data, **kwargs):
        headers = dict(kwargs.pop('headers', {}))
        headers['Content-Type'] = 'application/json'
        content = json.dumps(data).encode('utf8')
        super().__init__(content=content, headers=headers, **kwargs)

    def json(self):
        return json.loads(self.content.decode('utf8'))


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


# @pytest.mark.celery(broker_url=settings.CELERY_BROKER_URL, result_backend='rpc',)
@responses.activate
def test_search_cache(api, mocker, celery_app, celery_session_worker):
    from hoover.search.es import _index_name, DOCTYPE

    responses.add(
        responses.GET,
        'http://example.com/collections/testcol/json',
        json={
            "name": "testdata", "title": "testdata",
            "description": "testdata", "feed": "feed",
            "data_urls": "{id}/json", "stats": {},
            "max_result_window": 100, "refresh_interval": "6s",
        },
        status=200,
    )
    responses.add(
        responses.GET,
        'http://example.com/collections/testcol/modified_at',
        json={
            "modified_at": 1694173010,
            "age": 601791,
            "modified_data_at": 1692962263,
            "modified_tags_at": 1694173010,
        },
        status=200,
    )

    col = models.Collection.objects.create(
        name='testcol', index='hoover-testcol', public=True)
    col.save()

    # responses.add(responses.GET, 'http://search-es:9200/hoover-testcol/doc/mock1',
    es_search_resp = {'hits': {'hits': [{"_index": "hoover-testcol", "_type": "doc", "_id": "mock1", "_version": 1, "_seq_no": 1378, "_primary_term": 1, "found": True, "_source": {"content-type": "text/plain", "filetype": "text", "text": "text", "pgp": None, "ocr": None, "ocrtext": {}, "ocrpdf": None, "ocrimage": None, "has-thumbnails": False, "date": None, "date-created": None, "md5": "x", "sha1": "xx", "id": "mock1", "size": 8244, "filename": "tweety.pic", "path": "/art.zip//art/DECUS/tweety.pic", "path-text": "/art.zip//art/DECUS/tweety.pic", "path-parts": ["/art.zip", "/art.zip/", "/art.zip//art", "/art.zip//art/DECUS", "/art.zip//art/DECUS/tweety.pic"], "broken": [], "attachments": None, "word-count": 543, "_hoover": {"version": "2021-09-10T14:22:51.123683Z"}}}]}}
    es_search_resp_counts = {col.id: 1}

    def side_effect(*k, **v):
        time.sleep(1)
        return mocker.DEFAULT
    mocker.patch('hoover.search.es.search', return_value=(es_search_resp, es_search_resp_counts), side_effect=side_effect)

    assert {c['name'] for c in api.collections()} == {'testcol'}

    doc = MockDoc('mock1', {"content": {"id": "mock1", 'foo': "bar"}, "version": "1.12"})
    user = get_user_model()(username='fred', password='fred')
    user.save()

    search_q = {'match_all': {}}

    # These have refresh=False so we expect to only have 1 cache entry for all API calls
    for i in range(3):
        s1 = api.search(search_q, ['testcol'], user)
        hits = s1['hits']['hits']

        assert {hit['_id'] for hit in hits} == {'mock1'}
        assert hits[0]['_collection'] == 'testcol'

        s2 = api.async_search(search_q, ['testcol'], user)
        assert s2['collections'] == [col.name]
        assert s2['args']['collections'] == [col.name]
        assert s2['user'] == user.username
        assert s2['eta'] == {}
        assert s2['result'] == s1

        s3 = api.async_search_get(s2['task_id'], user, wait=True)
        assert s3 == s2

        assert models.SearchResultCache.objects.count() == 1, 'failed at iteration ' + str(i)

    models.SearchResultCache.objects.all().delete()

    # These have refresh=True so we expect to have many cache entry items
    for i in range(3):
        s1 = api.search(search_q, ['testcol'], user, refresh=True)
        hits = s1['hits']['hits']

        assert {hit['_id'] for hit in hits} == {'mock1'}
        assert hits[0]['_collection'] == 'testcol'

        s2 = api.async_search(search_q, ['testcol'], user, refresh=True)
        assert s2['collections'] == [col.name]
        assert s2['args']['collections'] == [col.name]
        assert s2['user'] == user.username
        assert s2['eta']['total_sec'] >= 0
        assert s2['result'] is None

        s3 = api.async_search_get(s2['task_id'], user, wait=True)
        assert s3['status'] == 'done'
        assert s3['result'] == s1

        assert models.SearchResultCache.objects.count() == (i + 1) * 2, 'failed at iteration ' + str(i)
