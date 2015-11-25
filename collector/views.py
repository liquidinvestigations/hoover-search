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
    return [c.slug for c in Collection.objects_for_user(request.user)]


def home(request):
    return render(request, 'home.html')


@csrf_exempt
def search(request):
    res = es.search(request.POST['q'], collection_slugs(request))
    return JsonResponse(res)
