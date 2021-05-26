from django.http import HttpResponse
from django.urls import reverse
import json
from .test_search import api
import pytest

pytestmark = pytest.mark.django_db


def test_search_rate(client, django_user_model):
    user = django_user_model.objects.create_user(username='testuser', password='pw')
    url = reverse('search')
    client.force_login(user)
    payload = {'query': {'match_all': {}}, 'collections': ['testcol']}
    for _ in range(30):
        resp = client.post(url, payload, content_type='application/json')
        assert resp.status_code == 200
    resp_exceeded = client.post(url, payload, content_type='application/json')
    assert resp_exceeded.status_code == 429
