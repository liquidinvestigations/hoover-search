import json
from django.shortcuts import render
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.core.urlresolvers import reverse
from . import es
from .models import Collection


class JsonResponse(HttpResponse):

    def __init__(self, data):
        return super(JsonResponse, self).__init__(
            json.dumps(data),
            content_type='application/json',
        )


def collection_slugs(user, collections_arg):
    rv = (c.slug for c in Collection.objects_for_user(user))
    if collections_arg is not None:
        collections = set(collections_arg)
        rv = (slug for slug in rv if slug in collections)
    return rv


def home(request):
    collections_arg = request.GET.get('collections')
    if collections_arg is not None:
        collections_arg = collections_arg.split()
    return render(request, 'home.html', {
        'collections': Collection.objects_for_user(request.user),
        'selected': set(collection_slugs(request.user, collections_arg)),
    })


@csrf_exempt
def collections(request):
    return JsonResponse([
        {'slug': col.slug, 'title': col.title}
        for col in Collection.objects_for_user(request.user)
    ])


@csrf_exempt
def search(request):
    body = json.loads(request.body)
    collections = list(collection_slugs(request.user, body.get('collections')))
    res = es.search(
        from_=body.get('from'),
        size=body.get('size'),
        query=body['query'],
        fields=body.get('fields'),
        highlight=body.get('highlight'),
        collections=collections,
    )
    return JsonResponse(res)


def whoami(request):
    return JsonResponse({
        'username': request.user.username,
        'admin': request.user.is_superuser,
        'urls': {
            'login': reverse('login'),
            'admin': reverse('admin:index'),
            'password_change': reverse('password_change'),
            'logout': reverse('logout') + '?next=' + reverse('home'),
        },
    })
