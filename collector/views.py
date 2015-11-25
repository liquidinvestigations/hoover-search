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


def collection_slugs(request):
    rv = (c.slug for c in Collection.objects_for_user(request.user))
    if 'collections' in request.GET:
        collections = set(request.GET['collections'].split())
        rv = (slug for slug in rv if slug in collections)
    return rv


def home(request):
    return render(request, 'home.html', {
        'collections': Collection.objects_for_user(request.user),
        'selected': set(collection_slugs(request)),
    })


@csrf_exempt
def search(request):
    res = es.search(request.POST['q'], list(collection_slugs(request)))
    return JsonResponse(res)
