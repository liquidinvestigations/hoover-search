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


def home(request):
    return render(request, 'home.html')


@csrf_exempt
def search(request):
    q = request.POST['q']

    cols = set(Collection.objects.filter(public=True))
    if request.user.id is not None:
        cols.update(Collection.objects.filter(users__id=request.user.id))

    collections = [col.slug for col in cols]
    r = es.search(q, collections)
    return JsonResponse(r)
