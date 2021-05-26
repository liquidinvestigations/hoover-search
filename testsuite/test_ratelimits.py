from django.http import HttpResponse
from django.urls import reverse
import json
from .test_search import api
import pytest

pytestmark = pytest.mark.django_db


def test_search_rate(api):
    for _ in range(30):
        api.search({'match_all': {}}, ['testcol'])['hits']['hits']
