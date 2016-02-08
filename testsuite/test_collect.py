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

    def search_ids(self, **data):
        res = self.post('/search', data).json()
        return set(hit['_id'] for hit in res['hits']['hits'])

@pytest.fixture
def api(client):
    return Api(client)

def delete_test_collections():
    from collector import es
    es.delete_all()
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

def collection_fixture(name, **kwargs):
    from django.conf import settings
    from collector import models, index, es
    col = models.Collection.objects.create(
        slug=name,
        options=json.dumps({
            'index': settings.FIXTURES_URL + '/' + name + '/collection.yaml',
        }),
        **kwargs
    )
    index.update_collection(col)
    es.refresh()
    return col

@clean_es
def test_collect(api):
    discworld = collection_fixture('discworld', public=True)
    hits = api.search_ids(query={'query_string': {'query': 'rincewind'}})
    assert hits == {'power_of_magic'}

    discworld.public = False
    discworld.save()
    hits = api.search_ids(query={'query_string': {'query': 'rincewind'}})
    assert hits == set()

@clean_es
def test_select_collections(api):
    discworld = collection_fixture('discworld', public=True)
    longearth = collection_fixture('longearth', public=True)
    hits = api.search_ids(query={'query_string': {'query': 'drum'}})
    assert hits == {'power_of_magic', 'long_war'}

    hits = api.search_ids(query={'query_string': {'query': 'drum'}},
        collections=['longearth'])
    assert hits == {'long_war'}

    longearth.public = False
    longearth.save()
    hits = api.search_ids(query={'query_string': {'query': 'drum'}})
    assert hits == {'power_of_magic'}
