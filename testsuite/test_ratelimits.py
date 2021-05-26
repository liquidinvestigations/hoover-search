from django.http import HttpResponse
from django.urls import reverse
import json
from .test_search import api
import pytest

pytestmark = pytest.mark.django_db


def test_search_rate(client):
    url = reverse('search')
    payload = {'query': {'match_all': {}}, 'collections': ['testcol']}
    for _ in range(30):
        resp = client.post(url, payload, content_type='application/json')
        assert resp.status_code == 200
