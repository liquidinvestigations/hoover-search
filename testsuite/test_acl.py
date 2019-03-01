import pytest

pytestmark = pytest.mark.django_db

def test_collections_acl_users(client):
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


def test_collections_acl_groups(client):
    from django.contrib.auth.models import User, AnonymousUser, Group
    from hoover.search.models import Collection
    from hoover.search.views import collections_acl
    anonymous = AnonymousUser()
    alice = User.objects.create_user('alice')
    bob = User.objects.create_user('bob')
    alice_group = Group.objects.create(name='alice1')
    alice_group.user_set.add(alice)
    foo = Collection.objects.create(name='foo', public=True)
    bar = Collection.objects.create(name='bar')
    baz = Collection.objects.create(name='baz')
    assert collections_acl(alice, ['foo', 'bar', 'baz']) == {foo}
    assert collections_acl(bob, ['foo', 'bar', 'baz']) == {foo}
    bar.groups.add(alice_group)
    assert collections_acl(alice, ['foo', 'bar', 'baz']) == {foo, bar}
    assert collections_acl(bob, ['foo', 'bar', 'baz']) == {foo}
    alice_group.user_set.add(bob)
    assert collections_acl(bob, ['foo', 'bar', 'baz']) == {foo, bar}
