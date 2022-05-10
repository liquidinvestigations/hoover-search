import pytest
import json
from django.urls import reverse
from django.contrib.auth.models import Group
from django.contrib.admin.sites import AdminSite
from hoover.search import models
from hoover.search.admin import CollectionAdmin


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


@pytest.fixture
def multi_collection(django_user_model):
    col1 = models.Collection.objects.create(name='testcol1',
                                            index='hoover-testcol1',
                                            )
    col2 = models.Collection.objects.create(name='testcolw',
                                            index='hoover-testcol1',
                                            )
    return (col1, col2)


@pytest.fixture
def collection_admin(multi_collection, django_user_model):
    admin = django_user_model.objects.create_user(username='admin', password='pw', is_staff=True)
    multi_collection[0].users.add(admin)
    return admin


def test_access_view(client, django_user_model, collection):
    url = reverse('collection_access', kwargs={'collection_name': 'testcol'})
    res = client.get(url)
    access_list = json.loads(res.content)
    assert access_list['testuser1'] == 'has individual access'
    assert access_list['testuser2'] == "has access through group 'testgroup'"
    assert access_list['testuser3'] == "has individual access, has access through group 'testgroup'"


def test_collection_queryset_superuser(admin_user, rf, multi_collection):
    request = rf.get('/admin')
    request.user = admin_user
    site = AdminSite()
    admin = CollectionAdmin(models.Collection, site)
    assert list(admin.get_queryset(request)) == list(models.Collection.objects.all())


def test_collection_queryset_admin(rf, collection_admin):
    request = rf.get('/admin')
    request.user = collection_admin
    site = AdminSite()
    admin = CollectionAdmin(models.Collection, site)
    assert list(admin.get_queryset(request)) == list(models.Collection.objects.all().filter(name='testcol1'))
