import pytest

pytestmark = pytest.mark.django_db

def test_can_search(client):
    from django.contrib.auth.models import AnonymousUser
    from hoover.search.models import Collection
    from hoover.search.views import can_search
    anonymous = AnonymousUser()
    foo = Collection.objects.create(name='foo', public=True)
    bar = Collection.objects.create(name='bar')
    assert can_search(anonymous, []) == set()
    assert can_search(anonymous, ['foo']) == {foo}
    assert can_search(anonymous, ['foo', 'bar']) == {foo}
    assert can_search(anonymous, ['foo', 'bar', 'foo', 'bar']) == {foo}
