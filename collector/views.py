import json
from django.shortcuts import render
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
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
        collections = set(collections_arg.split())
        rv = (slug for slug in rv if slug in collections)
    return rv


def home(request):
    collections_arg = request.GET.get('collections')
    return render(request, 'home.html', {
        'collections': Collection.objects_for_user(request.user),
        'selected': set(collection_slugs(request.user, collections_arg)),
    })


@csrf_exempt
def search(request):
    res = es.search(request.POST['q'], list(collection_slugs(request.user, None)))
    return JsonResponse(res)
