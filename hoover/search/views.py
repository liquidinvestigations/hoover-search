import json
from time import time
from django.shortcuts import render
from django.http import HttpResponse, Http404, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.core.urlresolvers import reverse
from django.urls.exceptions import NoReverseMatch
from django.conf import settings
from ..contrib import installed
from . import es
from .models import Collection
from . import signals
from .ratelimit import limit_user, get_request_limits


def JsonErrorResponse(reason, status=400):
    return JsonResponse({'status': 'error', 'reason': reason}, status=status)

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
    try:
        res, counts = es.search(**kwargs)
        res['status'] = 'ok'
    except es.SearchError as e:
        return JsonErrorResponse(e.reason)

    else:
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
            from_=body.get('from', 0),
            size=body.get('size', 10),
            query=body['query'],
            _source=body.get('_source'),
            post_filter=body.get('post_filter'),
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
        rv = collection.get_loader().get(id).view(request, suffix)
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
    urls = {
        'login': settings.LOGIN_URL,
        'admin': reverse('admin:index'),
        'logout': reverse('logout') + '?next=/',
    }
    try:
        password_change = reverse('password_change')
    except NoReverseMatch:
        pass
    else:
        urls['password_change'] = password_change
    return JsonResponse({
        'username': request.user.username,
        'admin': request.user.is_superuser,
        'urls': urls,
    })

@csrf_exempt
@limit_user
def batch(request):
    t0 = time()
    body = json.loads(request.body.decode('utf-8'))
    collections = collections_acl(request.user, body['collections'])
    query_strings = body.get('query_strings')
    aggs = body.get('aggs')

    if not collections:
        return JsonErrorResponse("No collections selected.")

    if not query_strings:
        return JsonErrorResponse("No items to be searched.")

    batch_limit = settings.HOOVER_BATCH_LIMIT
    if len(query_strings) > batch_limit:
        reason = "Too many queries. Limit is {}.".format(batch_limit)
        return JsonErrorResponse(reason)

    success = False
    try:
        res = es.batch_count(
            query_strings,
            collections,
            aggs
        )
        res['status'] = 'ok'
        success = True
        return JsonResponse(res)

    except es.SearchError as e:
        return JsonErrorResponse(e.reason)

    finally:
        signals.batch.send('hoover.batch', **{
            'request': request,
            'collections': collections,
            'duration': time() - t0,
            'success': success,
            'query_count': len(query_strings),
        })


def is_staff(request):
    if request.user.is_staff:
        return JsonResponse({'is_staff': True}, status=200)
    else:
        return JsonResponse({'is_staff': False}, status=403)


def limits(request):
    """ Get rate limits """
    return JsonResponse({
        'batch': settings.HOOVER_BATCH_LIMIT,
        'requests': get_request_limits(request.user),
    })
