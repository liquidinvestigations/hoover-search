import json
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

@pytest.fixture
def api(client):
    return Api(client)

def test_collect(api):
    from collector import models, index, es
    from django.conf import settings
    es.delete('discworld')
    col = models.Collection.objects.create(
        slug='discworld',
        options=json.dumps({
            'index': settings.FIXTURES_URL + '/discworld/collection.yaml',
        }),
        public=True,
    )
    index.update_collection(col)
    es.refresh()
    res = api.post('/search', {
        'query': {'query_string': {'query': 'rincewind'}},
    }).json()
    [hit] = res['hits']['hits']
    assert hit['_id'] == 'discworld/power_of_magic'
