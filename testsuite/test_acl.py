import pytest

pytestmark = pytest.mark.django_db

def test_collections_acl(client):
    from django.contrib.auth.models import User, AnonymousUser
    from hoover.search.models import Collection
    from hoover.search.views import collections_acl
    anonymous = AnonymousUser()
    alice = User.objects.create_user('alice')
    foo = Collection.objects.create(name='foo', public=True)
    bar = Collection.objects.create(name='bar')
    baz = Collection.objects.create(name='baz')
    assert collections_acl(anonymous, []) == set()
    assert collections_acl(anonymous, ['foo']) == {foo}
    assert collections_acl(anonymous, ['foo', 'bar', 'baz']) == {foo}
    assert collections_acl(anonymous, ['foo', 'bar', 'foo', 'bar']) == {foo}
    assert collections_acl(alice, []) == set()
    assert collections_acl(alice, ['foo', 'bar', 'baz']) == {foo}
    baz.users.add(alice)
    assert collections_acl(alice, ['foo', 'bar', 'baz']) == {foo, baz}
