import json
import functools
import pytest

pytestmark = pytest.mark.django_db

class Api:

    def __init__(self, client):
        self.client = client

    def post(self, url, data):
        return self.client.post(
            '/search',
            data=json.dumps(data).encode('utf-8'),
            content_type='application/json',
        )

    def search_ids(self, query):
        res = self.post('/search', {'query': query}).json()
        return set(hit['_id'] for hit in res['hits']['hits'])

@pytest.fixture
def api(client):
    return Api(client)

def delete_test_collections():
    from collector import es
    es.delete('discworld')
    es.delete('longearth')
    es.refresh()

def clean_es(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        delete_test_collections()
        try:
            return func(*args, **kwargs)
        finally:
            try: delete_test_collections()
            except: pass
    return wrapper

@clean_es
def test_collect(api):
    from collector import models, index, es
    from django.conf import settings
    col = models.Collection.objects.create(
        slug='discworld',
        options=json.dumps({
            'index': settings.FIXTURES_URL + '/discworld/collection.yaml',
        }),
        public=True,
    )
    index.update_collection(col)
    es.refresh()
    hits = api.search_ids({'query_string': {'query': 'rincewind'}})
    assert hits == {'discworld/power_of_magic'}

@clean_es
def test_private_collection(api):
    from collector import models, index, es
    from django.conf import settings
    discworld = models.Collection.objects.create(
        slug='discworld',
        options=json.dumps({
            'index': settings.FIXTURES_URL + '/discworld/collection.yaml',
        }),
        public=True,
    )
    index.update_collection(discworld)
    longearth = models.Collection.objects.create(
        slug='longearth',
        options=json.dumps({
            'index': settings.FIXTURES_URL + '/longearth/collection.yaml',
        }),
        public=True,
    )
    index.update_collection(longearth)
    es.refresh()
    hits = api.search_ids({'query_string': {'query': 'drum'}})
    assert hits == {'discworld/power_of_magic', 'longearth/long_war'}

    longearth.public = False
    longearth.save()
    hits = api.search_ids({'query_string': {'query': 'drum'}})
    assert hits == {'discworld/power_of_magic'}
