import json
from urllib.parse import quote
from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse, HttpResponseRedirect, Http404
from django.views.decorators.csrf import csrf_exempt
from django.core.urlresolvers import reverse
from django.conf import settings
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


def ping(request):
    Collection.objects.count()
    return HttpResponse('ok\n')


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

    from .es import _index_id
    def col_name(id):
        return Collection.objects.get(id=id).name

    for item in res['hits']['hits']:
        item['_collection'] = col_name(_index_id(item['_index']))
    res['count_by_index'] = {
        col_name(i): counts[i]
        for i in counts
    }
    return JsonResponse(res)


def doc(request, collection_name, id):
    collection = get_object_or_404(
        Collection.objects_for_user(request.user),
        name=collection_name,
    )

    try:
        es_doc = collection.get_document(id)
    except es.TransportError:
        raise Http404

    mime_type = es_doc['_source'].get('mime_type')
    doc = collection.get_loader().get_document(es_doc)

    if request.GET.get('raw') == 'on':
        with doc.open() as tmp:
            return HttpResponse(tmp.read(), content_type=mime_type)

    else:
        if settings.HOOVER_PDFJS_URL and mime_type == 'application/pdf':
            raw = request.build_absolute_uri() + '?raw=on'
            url = settings.HOOVER_PDFJS_URL + 'viewer.html?file=' + quote(raw)
            return HttpResponseRedirect(url)

        else:
            html = doc.html()
            if settings.EMBED_HYPOTHESIS:
                html += '\n' + settings.EMBED_HYPOTHESIS
            return HttpResponse(html)


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
