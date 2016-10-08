import pytest

pytestmark = pytest.mark.django_db

def test_can_search(client):
    from django.contrib.auth.models import User, AnonymousUser
    from hoover.search.models import Collection
    from hoover.search.views import can_search
    anonymous = AnonymousUser()
    alice = User.objects.create_user('alice')
    foo = Collection.objects.create(name='foo', public=True)
    bar = Collection.objects.create(name='bar')
    baz = Collection.objects.create(name='baz')
    assert can_search(anonymous, []) == set()
    assert can_search(anonymous, ['foo']) == {foo}
    assert can_search(anonymous, ['foo', 'bar', 'baz']) == {foo}
    assert can_search(anonymous, ['foo', 'bar', 'foo', 'bar']) == {foo}
    assert can_search(alice, []) == set()
    assert can_search(alice, ['foo', 'bar', 'baz']) == {foo}
    baz.users.add(alice)
    assert can_search(alice, ['foo', 'bar', 'baz']) == {foo, baz}
