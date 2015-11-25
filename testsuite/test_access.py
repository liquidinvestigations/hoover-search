import pytest

pytestmark = pytest.mark.django_db


def collections(body):
    if 'or' in body['query']['filtered']['filter']:
        return sorted(
            item['term']['collection']
            for item in body['query']['filtered']['filter']['or']
        )

    else:
        assert body['query']['filtered']['filter'] == {
            'bool': {'must_not': {'match_all': {}}},
        }
        return []


def test_access(monkeypatch, client):
    import json
    from django.contrib.auth.models import User
    from collector.models import Collection
    from collector import es

    class MockEs(object):
        def search(self, index, body):
            return body

    monkeypatch.setattr(es, 'es', MockEs())

    Collection.objects.all().delete()
    c1 = Collection.objects.create(slug='c1')
    c2 = Collection.objects.create(slug='c2')
    c3 = Collection.objects.create(slug='c3')
    u = User.objects.create_user(username='u', password='p')
    c2.users = [u]
    c2.save()

    def search(q):
        return json.loads(client.post('/search', {'q': q}).content)

    # no login; should not search in any collection
    assert collections(search('foo')) == []

    # no login; should search in c1 only
    c1.public = True
    c1.save()
    assert collections(search('foo')) == ['c1']

    # logged in; should search in c1 and c2
    assert client.login(username='u', password='p')
    assert collections(search('foo')) == ['c1', 'c2']
