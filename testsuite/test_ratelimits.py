from django.http import HttpResponse
from django.urls import reverse
import json
from .test_search import external, JsonResponse
import pytest
from time import sleep
from hoover.search import models
import responses
import requests
import logging

pytestmark = pytest.mark.django_db


@pytest.fixture
def test_collection():
    col = models.Collection.objects.create(
        name='testcol',
        index='hoover-testcol',
        public=True,
        loader='hoover.search.loaders.external.Loader',
        options='{"url": "https://example.com/doc/json"}',
    )
    return col


def test_search_rate(client, django_user_model):
    user = django_user_model.objects.create_user(username='testuser', password='pw')
    url = reverse('search')
    client.force_login(user)
    payload = {'query': {'match_all': {}}, 'collections': ['testcol']}
    for _ in range(30):
        resp = client.post(url, payload, content_type='application/json')
        assert resp.status_code == 200
    resp_exceeded = client.post(url, payload, content_type='application/json')
    logging.warning(resp_exceeded)
    assert resp_exceeded.status_code == 429
    sleep(60)
    resp_after_timeout = client.post(url, payload, content_type='application/json')
    assert resp_after_timeout.status_code == 200


@pytest.mark.skip(
    reason='not working yet')
def test_search_doc(client, django_user_model, test_collection):
    user = django_user_model.objects.create_user(username='testuser', password='pw')
    client.force_login(user)

    external['https://example.com/doc/json'] = JsonResponse({
        'data_urls': '{id}/json',
    })

    external['https://example.com/doc/mock1/json'] = JsonResponse({
        'id': 'mock1',
        'version': '1',
        'content': {'text': "hello world"},
    })

    for _ in range(30):
        resp = client.post('/doc/testcol/mock1/json')
        assert resp.status_code == 200
    resp_exceeded = client.post('/doc/testcol/mock1/json')
    assert resp_exceeded.status_code == 429
    sleep(60)
    resp_after_timeout = client.post('/doc/testcol/mock1/json')
    assert resp_after_timeout == 200
