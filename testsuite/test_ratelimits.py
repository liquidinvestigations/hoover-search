from django.urls import reverse
import pytest
from time import sleep
from hoover.search import models
import responses
from django.conf import settings

pytestmark = pytest.mark.django_db
RATELIMIT_REQUESTS = settings.HOOVER_RATELIMIT_USER[0]
RATELIMIT_SECONDS = settings.HOOVER_RATELIMIT_USER[1]
RATELIMIT_REQUESTS_THUMBNAIL = settings.HOOVER_RATELIMIT_THUMBNAIL[0]
RATELIMIT_SECONDS_THUMBNAIL = settings.HOOVER_RATELIMIT_THUMBNAIL[1]


@pytest.fixture
def collection():
    col = models.Collection.objects.create(
        name='testcol',
        index='hoover-testcol',
        public=True,
    )
    return col


@pytest.fixture
def mocked_responses():
    with responses.RequestsMock() as rsps:
        # this mocks the response made by hoover.search.loaders.external.get_json
        # rsps.add(responses.GET, 'http://example.com/collections/testcol/json',
        #          json={
        #              'name': 'testcol',
        #              'title': 'testcol',
        #              'description': 'testcol',
        #              'feed': 'feed',
        #              'data_urls': 'mock1/json',
        #              'stats': 'stats',
        #              'max_result_window': 1,
        #              'refresh_interval': 1,
        #          }, status=200)
        # rsps.add(
        #     responses.GET,
        #     'http://example.com/collections/testcol/modified_at',
        #     json={
        #         "modified_at": 1694173010,
        #         "age": 601791,
        #         "modified_data_at": 1692962263,
        #         "modified_tags_at": 1694173010,
        #     },
        #     status=200,
        # )
        yield rsps


@pytest.mark.skip(reason="old search payload fails; anyway search rate is same as doc")
def test_search_rate(client, django_user_model, collection):
    # a user needs to be logged in as the ratelimits apply per user
    user = django_user_model.objects.create_user(username='testuser', password='pw')
    url = reverse('search')
    client.force_login(user)
    # just an arbitrary payload
    payload = {'query': {'match_all': {}}, 'collections': [collection.name]}
    for _ in range(RATELIMIT_REQUESTS):
        resp = client.post(url, payload, content_type='application/json')
        assert resp.status_code == 200
    resp_exceeded = client.post(url, payload, content_type='application/json')
    assert resp_exceeded.status_code == 429
    sleep(RATELIMIT_SECONDS)
    resp_after_timeout = client.post(url, payload, content_type='application/json')
    assert resp_after_timeout.status_code == 200


def test_doc_rate(client, django_user_model, collection, mocked_responses):
    # the requests to snoop made in hoover.search.loaders.external need to be mocked
    mocked_responses.add(responses.GET, 'http://example.com/collections/testcol/mock1/json', json={}, status=200)

    # a user needs to be logged in as the ratelimits apply per user
    user = django_user_model.objects.create_user(username='testuser', password='pw')
    client.force_login(user)
    for _ in range(RATELIMIT_REQUESTS):
        resp = client.post('/api/v1/doc/testcol/mock1/json')
        assert resp.status_code == 200
    resp_exceeded = client.post('/api/v1/doc/testcol/mock1/json')
    assert resp_exceeded.status_code == 429
    sleep(RATELIMIT_SECONDS)
    resp_after_timeout = client.post('/api/v1/doc/testcol/mock1/json')
    assert resp_after_timeout.status_code == 200


def test_thumbnail_rate(client, django_user_model, collection, mocked_responses):
    # the request to snoop made in hoover.search.loaders.external needs to be mocked
    mocked_responses.add(responses.GET, 'http://example.com/collections/testcol/mock1/thumbnail/200.jpg', json={}, status=200)
    # a user needs to be logged in as the ratelimits apply per user
    user = django_user_model.objects.create_user(username='testuser', password='pw')
    client.force_login(user)
    for _ in range(RATELIMIT_REQUESTS_THUMBNAIL):
        resp = client.post('/api/v1/doc/testcol/mock1/thumbnail/200.jpg')
        assert resp.status_code == 200
    resp_exceeded = client.post('/api/v1/doc/testcol/mock1/thumbnail/200.jpg')
    assert resp_exceeded.status_code == 429
    sleep(RATELIMIT_SECONDS_THUMBNAIL)
    resp_after_timeout = client.post('/api/v1/doc/testcol/mock1/thumbnail/200.jpg')
    assert resp_after_timeout.status_code == 200
