import json
from django.shortcuts import render
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from . import es


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
    r = es.search(q)
    return JsonResponse(r)
