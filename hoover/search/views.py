import json
from time import time
from urllib.parse import quote
import mimetypes
from pathlib import Path
from django.shortcuts import render, get_object_or_404
from django.http import (HttpResponse, HttpResponseRedirect, Http404,
    FileResponse, JsonResponse)
from django.views.decorators.csrf import csrf_exempt
from django.core.urlresolvers import reverse
from django.conf import settings
from ..contrib import installed
from . import es
from .models import Collection
from . import signals

if installed.ratelimit:
    from ..contrib.ratelimit.decorators import limit_user
else:
    limit_user = lambda func: func

def collections_acl(user, collections_arg):
    available = list(Collection.objects_for_user(user))
    requested = set(collections_arg)
    return set(col for col in available if col.name in requested)

def ping(request):
    Collection.objects.count()
    return HttpResponse('ok\n')

def home(request):
    return render(request, 'home.html')

@csrf_exempt
def collections(request):
    return JsonResponse([
        {'name': col.name, 'title': col.title}
        for col in Collection.objects_for_user(request.user)
    ], safe=False)

def _search(request, **kwargs):
    res, counts = es.search(**kwargs)

    from .es import _index_id
    def col_name(id):
        return Collection.objects.get(id=id).name

    for item in res['hits']['hits']:
        name = col_name(_index_id(item['_index']))
        url = 'doc/{}/{}'.format(name, item['_id'])
        item['_collection'] = name
        item['_url'] = request.build_absolute_uri(url)
    res['count_by_index'] = {
        col_name(i): counts[i]
        for i in counts
    }
    return JsonResponse(res)

@csrf_exempt
@limit_user
def search(request):
    t0 = time()
    body = json.loads(request.body.decode('utf-8'))
    collections = collections_acl(request.user, body['collections'])

    success = False
    try:
        response = _search(
            request,
            from_=body.get('from'),
            size=body.get('size'),
            query=body['query'],
            fields=body.get('fields'),
            sort=body.get('sort', ['_score']),
            aggs=body.get('aggs', {}),
            highlight=body.get('highlight'),
            collections=[c.name for c in collections],
        )
        success = True
        return response

    finally:
        signals.search.send('hoover.search', **{
            'request': request,
            'collections': collections,
            'duration': time() - t0,
            'success': success,
        })

@limit_user
def doc(request, collection_name, id, suffix):
    for collection in Collection.objects_for_user(request.user):
        if collection.name == collection_name:
            break
    else:
        raise Http404
    t0 = time()
    success = False
    try:
        rv = collection.get_loader().get(id + suffix).view(request)
        success = True
        return rv

    finally:
        signals.doc.send('hoover.search', **{
            'request': request,
            'collection': collection,
            'doc_id': id,
            'duration': time() - t0,
            'success': success,
        })

def whoami(request):
    return JsonResponse({
        'username': request.user.username,
        'admin': request.user.is_superuser,
        'urls': {
            'login': settings.LOGIN_URL,
            'admin': reverse('admin:index'),
            'password_change': reverse('password_change'),
            'logout': reverse('logout') + '?next=/',
        },
    })

def _resolve_ui_file(filename):
    ui_root = Path(settings.HOOVER_UI_ROOT)
    file = ui_root / filename
    if not (ui_root == file or ui_root in file.parents):
        raise Http404()

    if file.is_dir():
        file = file / 'index.html'

    if file.is_file():
        return file

    raise Http404()

def _serve_ui_file(file):
    content_type = mimetypes.guess_type(str(file))[0] or None
    return FileResponse(file.open('rb'), content_type=content_type)

def serve_ui(request, filename):
    return _serve_ui_file(_resolve_ui_file(filename))
