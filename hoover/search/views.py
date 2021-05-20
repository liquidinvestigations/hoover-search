import json
import os
import urllib.parse
from time import time
from django.shortcuts import render, redirect
from django.http import HttpResponse, Http404, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.urls import reverse
from django.urls.exceptions import NoReverseMatch
from django.conf import settings
from . import es
from .models import Collection
from . import signals
import requests
import re
from ratelimit.decorators import ratelimit


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


def collections(request):
    return JsonResponse([
        {'name': col.name, 'title': col.title, 'stats': col.get_meta()['stats']}
        for col in Collection.objects_for_user(request.user)
    ], safe=False)


def search_fields(request):
    assert request.user
    assert request.user.username
    return JsonResponse({
        'fields': es.get_fields(request.user.profile.uuid),
    }, safe=False)


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


def _check_fields(query_fields, allowed_fields):
    all_fields = allowed_fields['all'] + allowed_fields['_source']
    for x in query_fields:
        x = x.replace('.*', '')
        assert x in all_fields, 'field not recognized'


@csrf_exempt
@ratelimit(key='user', rate=settings.HOOVER_RATELIMIT_USER)
def search(request):
    t0 = time()
    body = json.loads(request.body.decode('utf-8'))
    collections = collections_acl(request.user, body['collections'])
    source_fields = body.get('_source', [])
    query_fields = body['query'].get('fields', [])
    _check_fields(source_fields + query_fields,
                  es.get_fields(request.user.profile.uuid))

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
            search_after=body.get('search_after'),
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


def thumbnail_rate(group, request):
    has_thumbnail = re.search(r'/thumbnail/\d{3}/.jpg$', request.path)
    if has_thumbnail:
        return (1000, 60)
    return settings.HOOVER_RATELIMIT_USER


@ratelimit(key='user', rate=thumbnail_rate)
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


@csrf_exempt
@ratelimit(key='user', rate=settings.HOOVER_RATELIMIT_USER)
def doc_tags(request, collection_name, id, suffix):
    for collection in Collection.objects_for_user(request.user):
        if collection.name == collection_name:
            break
    else:
        print('collection 404')
        raise Http404

    username = request.user.username
    assert username
    user_uuid = request.user.profile.uuid
    assert user_uuid
    url = settings.SNOOP_BASE_URL + f"/collections/{collection_name}/{id}/tags/{username}/{user_uuid}{suffix}"
    r = requests.request(
        method=request.method,
        url=url,
        data=request.body,
        params=request.GET or request.POST,
        cookies=request.COOKIES,
        headers=request.headers,
    )

    return HttpResponse(
        r.content,
        content_type=r.headers.get('Content-Type'),
        status=r.status_code,
        reason=r.reason,
    )


def whoami(request):
    if settings.HOOVER_AUTHPROXY:
        logout_url = "/oauth2/sign_out?rd=" + urllib.parse.quote(str(os.getenv('LIQUID_CORE_LOGOUT_URL')), safe='')
    else:
        logout_url = reverse('logout') + '?next=/'

    urls = {
        'login': settings.LOGIN_URL,
        'admin': reverse('admin:index'),
        'logout': logout_url,
        'hypothesis_embed': settings.HOOVER_HYPOTHESIS_EMBED,
    }
    try:
        password_change = reverse('password_change')
    except NoReverseMatch:
        pass
    else:
        urls['password_change'] = password_change

    if request.user.is_authenticated:
        uuid = request.user.profile.uuid
    else:
        uuid = None
    return JsonResponse({
        'username': request.user.username,
        'uuid': uuid,
        'admin': request.user.is_superuser,
        'urls': urls,
        'title': settings.HOOVER_TITLE,
        'liquid': {
            'title': settings.HOOVER_LIQUID_TITLE,
            'url': settings.HOOVER_LIQUID_URL,
        },
    })


@csrf_exempt
@ratelimit(key='user', rate=settings.HOOVER_RATELIMIT_USER)
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
        'requests': {
            'interval': settings.HOOVER_RATELIMIT_USER[1],
            'limit': settings.HOOVER_RATELIMIT_USER[0],
            'count': 0,
        },
    })


def doc_redirect_v0(request, collection_name, id, suffix):
    # the target path is actually served by the UI, not us:
    redirect_url = f'/doc/{collection_name}/{id}'
    return redirect(redirect_url, permanent=True)


def web_viewer_redirect_v0(request):
    relative_path = request.GET['file']
    # this path looks like /api/v0/doc/testdata/8319fde068733d8.../...
    collection, identifier = relative_path.split('/', 6)[4:6]
    # the target path is actually served by the UI, not us:
    redirect_url = f'/doc/{collection}/{identifier}'
    return redirect(redirect_url, permanent=True)
