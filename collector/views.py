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


def collection_names(user, collections_arg):
    rv = (c.name for c in Collection.objects_for_user(user))
    if collections_arg is not None:
        collections = set(collections_arg)
        rv = (name for name in rv if name in collections)
    return rv


def home(request):
    collections_arg = request.GET.get('collections')
    if collections_arg is not None:
        collections_arg = collections_arg.split()
    return render(request, 'home.html', {
        'collections': Collection.objects_for_user(request.user),
        'selected': set(collection_names(request.user, collections_arg)),
    })


@csrf_exempt
def collections(request):
    return JsonResponse([
        {'name': col.name, 'title': col.title}
        for col in Collection.objects_for_user(request.user)
    ])


@csrf_exempt
def search(request):
    body = json.loads(request.body.decode('utf-8'))
    collections = list(collection_names(request.user, body.get('collections')))
    res, counts = es.search(
        from_=body.get('from'),
        size=body.get('size'),
        query=body['query'],
        fields=body.get('fields'),
        highlight=body.get('highlight'),
        collections=collections,
    )
    res['count_by_index'] = {
        Collection.objects.get(id=i).name: counts[i]
        for i in counts
    }
    return JsonResponse(res)


def doc(request, collection_name, id):
    # TODO make sure user can access collection
    collection = Collection.objects.get(name=collection_name)
    es_doc = collection.get_document(id)
    mime_type = es_doc['_source'].get('mime_type')
    doc = collection.get_loader().get_document(es_doc)

    if request.GET.get('raw') == 'on':
        with doc.open() as tmp:
            return HttpResponse(tmp.read(), content_type=mime_type)

    else:
        return HttpResponse(doc.html())


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
