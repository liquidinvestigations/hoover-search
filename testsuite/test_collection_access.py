import pytest
import json
from django.urls import reverse
from django.contrib.auth.models import Group
from hoover.search import models


@pytest.fixture
def collection(django_user_model):
    user1 = django_user_model.objects.create_user(username='testuser1', password='pw')
    user2 = django_user_model.objects.create_user(username='testuser2', password='pw')
    user3 = django_user_model.objects.create_user(username='testuser3', password='pw')
    group = Group.objects.create(name='testgroup')
    user2.groups.add(group)
    user3.groups.add(group)
    col = models.Collection.objects.create(
        name='testcol',
        index='hoover-testcol',
        public=True,
    )
    col.save()
    col.users.add(user1)
    col.users.add(user3)
    col.groups.add(group)
    return col


def test_access_view(client, django_user_model, collection):
    url = reverse('collection_access', kwargs={'collection_name': 'testcol'})
    res = client.get(url)
    access_list = json.loads(res.content)
    assert access_list['testuser1'] == 'has individual access'
    assert access_list['testuser2'] == "has access through group 'testgroup'"
    assert access_list['testuser3'] == "has individual access, has access through group 'testgroup'"
