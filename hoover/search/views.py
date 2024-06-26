from datetime import timedelta
import datetime
import logging
import json
import os
import urllib.parse
from time import time
from django.shortcuts import render, redirect
from django.http import HttpResponse, Http404, JsonResponse
from django.http import HttpResponseForbidden
from django.views.decorators.csrf import csrf_exempt
from django.urls import reverse
from django.urls.exceptions import NoReverseMatch
from django.conf import settings
from django.views.defaults import permission_denied
from django.core.exceptions import PermissionDenied
from django.utils import timezone
from django.views.decorators.cache import cache_control, never_cache
from . import es
from . import models
from .models import Collection, NextcloudCollection
from . import signals
from . import celery as cel
import requests
import re
from django_ratelimit.decorators import ratelimit
from django_ratelimit.exceptions import Ratelimited

from hoover.search.tracing import Tracer
tracer = Tracer(__name__)

log = logging.getLogger(__name__)
SEARCH_KEY = 'hoover.search.search'
BATCH_KEY = 'hoover.search.batch_search'

# keep results valid for this interval
SEARCH_CACHE_AGE = timedelta(hours=8)
BATCH_CACHE_AGE = timedelta(hours=12)

# join refreshed/recent requests with
SEARCH_CACHE_JOIN_RUNNING_MAX_AGE = timedelta(minutes=4)
BATCH_CACHE_JOIN_RUNNING_MAX_AGE = timedelta(minutes=15)

# time to wait for celery task to finish
SEARCH_SYNC_WAIT_FOR_RESULTS = timedelta(minutes=2)
BATCH_SYNC_WAIT_FOR_RESULTS = timedelta(minutes=5)

BASIC_VIEW_CACHE_OPT = dict(
    private=True,
    max_age=60,
    stale_while_revalidate=60,
)


# ================================================================================
#                                HELPERS
# ================================================================================

def JsonErrorResponse(reason, status=400):
    return JsonResponse({'status': 'error', 'reason': reason}, status=status)


def collections_acl(user, collections_arg, empty_ok=False):
    if empty_ok and not collections_arg:
        return set()
    requested = set(collections_arg)
    assert len(requested) > 0, 'no collections selected'
    available = list(Collection.objects_for_user(user))
    approved = set(col for col in available if col.name in requested)
    if not approved:
        msg = 'collections not found or access denied: ' + str(collections_arg)
        raise PermissionDenied(msg)
    return approved


def nextcloud_collections(request):
    return JsonResponse([
        {
            'webdav_url': col.url,
            'webdav_username': col.username,
            'webdav_password': col.password,
            'name': col.name,
            'process': True,
            'sync': False,
            'ocr_languages': '',
            'max_result_window': 100000,
            'refresh_interval': '1s',
            'pdf_preview_enabled': False,
            'thumbnail_generator_enabled': False,
            'image_classification_object_detection_enabled': False,
            'image_classification_classify_images_enabled': False,
            'nlp_language_detection_enabled': False,
            'nlp_fallback_language': 'en',
            'nlp_entity_extraction_enabled': False,
            'translation_enabled': False,
            'translation_target_languages': 'en',
            'translation_text_length_limit': 400,
            'default_table_header': '',
            'explode_table_rows': False,
            's3_blobs_address': '',
            's3_blobs_access_key': '',
            's3_blobs_secret_key': '',
        }
        for col in NextcloudCollection.objects.all()
    ], safe=False)


def _sanitize_utf8_values(value):
    """Ensure UTF-8 strings have valid encodings in dict.

    Needed to avoid errors down the line when trying to put the search output into Postgres."""

    if isinstance(value, str):
        fixed_str = _fix_string(value)
        if fixed_str != value:
            log.warning('SANITIZE value: old=%s new=%s', value, fixed_str)
        return fixed_str
    elif isinstance(value, list):
        return [_sanitize_utf8_values(x) for x in value]
    elif isinstance(value, dict):
        return {k: _sanitize_utf8_values(v) for k, v in value.items()}
    else:
        return value


def _fix_string(s):
    """Fix potential encoding errors for this UTF-8 string."""
    return s.encode('utf-8', errors='replace').decode('utf-8', errors='replace')
    # return s.encode('utf-16', 'surrogatepass')\
    #     .decode('utf-16', errors='replace')\
    #     .encode('utf-8', errors='backslashreplace')\
    #     .decode('utf-8', errors='replace')


def _check_fields(query_fields, allowed_fields):
    all_fields = allowed_fields['all'] + allowed_fields['_source']
    for x in query_fields:
        x = x.replace('.*', '')
        assert x in all_fields, 'field not recognized'


def rates(group, request):
    if settings.HOOVER_RATELIMIT_USER:
        return (settings.HOOVER_RATELIMIT_USER[0], settings.HOOVER_RATELIMIT_USER[1])
    else:
        return None


# ================================================================================
#                                BASIC VIEWS
# ================================================================================

# these views don't have any user data and can be cached on the browser side for
# a minute or two, to limit the request count and browsing lag because of these 5-6
# new connections every tab

@cache_control(**BASIC_VIEW_CACHE_OPT)
def ping(request):
    Collection.objects.count()
    return HttpResponse('ok\n')


@cache_control(**BASIC_VIEW_CACHE_OPT)
def home(request):
    return render(request, 'home.html')


@cache_control(**BASIC_VIEW_CACHE_OPT)
@ratelimit(key='user', rate=rates, block=True)
def collections(request):
    return JsonResponse([
        {'name': col.name, 'title': col.title, 'stats': col.stats or dict()}
        for col in Collection.objects_for_user(request.user)
    ], safe=False)


@cache_control(**BASIC_VIEW_CACHE_OPT)
@ratelimit(key='user', rate=rates, block=True)
def search_fields(request):
    assert request.user
    assert request.user.username
    return JsonResponse({
        'fields': es.get_fields(request.user.profile.uuid),
    }, safe=False)


@cache_control(**BASIC_VIEW_CACHE_OPT)
@ratelimit(key='user', rate=rates, block=True)
def is_staff(request):
    if request.user.is_staff:
        return JsonResponse({'is_staff': True}, status=200)
    else:
        return JsonResponse({'is_staff': False}, status=403)


@cache_control(**BASIC_VIEW_CACHE_OPT)
@ratelimit(key='user', rate=rates, block=True)
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


@cache_control(**BASIC_VIEW_CACHE_OPT)
@ratelimit(key='user', rate=rates, block=True)
def collection_access(request, collection_name):
    '''View that returns a list of users who can access a collection.

    Returns a JsonResponse with usernames and the reasons why that user can access
    the collection. The reasons can be individual access or access through a group.
    '''
    col = list(collections_acl(request.user, [collection_name]))
    if not col:
        raise Http404
    col = col[0]
    user_list = {}
    for u in col.users.all():
        user_list[u.username] = 'has individual access'
    for group in col.groups.all():
        for u in group.user_set.all():
            description = f"has access through group '{group.name}'"
            if u.username not in user_list:
                user_list[u.username] = description
            else:
                user_list[u.username] = user_list[u.username] + ', ' + description
    return JsonResponse(user_list)


@tracer.wrap_function()
@cache_control(**BASIC_VIEW_CACHE_OPT)
@ratelimit(key='user', rate=rates, block=True)
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


# ================================================================================
#                                SEARCH VIEWS
# ================================================================================

# These views shouldn't be cached - we have our own caching mechanism.

@tracer.wrap_function()
@csrf_exempt
@never_cache
@ratelimit(key='user', rate=rates, block=True)
def search(request):
    """API view that fetches search results.

    All permission checks for users and fields must be handled here. Then, `_cached_search` is called to
    actually run the search and return results.
    """

    t0 = time()
    body = json.loads(request.body.decode('utf-8'))
    collections = collections_acl(request.user, body['collections'])
    dedup_collections = collections_acl(request.user, body.get('dedup_collections', []), empty_ok=True)
    source_fields = body.get('_source', [])
    query_fields = body['query'].get('fields', [])
    _check_fields(source_fields + query_fields,
                  es.get_fields(request.user.profile.uuid))
    refresh = bool(request.GET.get('refresh', None))

    success = False
    try:
        args = dict(
            from_=body.get('from', 0),
            size=body.get('size', 10),
            query=body['query'],
            _source=body.get('_source'),
            post_filter=body.get('post_filter'),
            sort=body.get('sort', ['_score']),
            aggs=body.get('aggs', {}),
            highlight=body.get('highlight'),
            collections=[c.name for c in collections],
            dedup_collections=[c.name for c in dedup_collections],
            search_after=body.get('search_after'),
        )
        cache_entry = _cached_search(collections, request.user, args,
                                     refresh=refresh, wait=True)
        response = cache_entry.result
        response['status'] = 'ok'
        success = True
        return JsonResponse(response)

    finally:
        signals.search.send('hoover.search', **{
            'request': request,
            'collections': collections,
            'duration': time() - t0,
            'success': success,
        })


@tracer.wrap_function()
@csrf_exempt
@never_cache
@ratelimit(key='user', rate=rates, block=True)
def async_search(request):
    """API view that fetches search results.

    All permission checks for users and fields must be handled here. Then, `_cached_search` is called to
    actually run the search and return results.
    """

    t0 = time()
    body = json.loads(request.body.decode('utf-8'))
    collections = collections_acl(request.user, body['collections'])
    dedup_collections = collections_acl(request.user, body.get('dedup_collections', []), empty_ok=True)
    source_fields = body.get('_source', [])
    query_fields = body['query'].get('fields', [])
    _check_fields(source_fields + query_fields,
                  es.get_fields(request.user.profile.uuid))
    refresh = bool(request.GET.get('refresh', None))

    success = False
    try:
        args = dict(
            from_=body.get('from', 0),
            size=body.get('size', 10),
            query=body['query'],
            _source=body.get('_source'),
            post_filter=body.get('post_filter'),
            sort=body.get('sort', ['_score']),
            aggs=body.get('aggs', {}),
            highlight=body.get('highlight'),
            collections=[c.name for c in collections],
            dedup_collections=[c.name for c in dedup_collections],
            search_after=body.get('search_after'),
        )
        cache_entry = _cached_search(collections, request.user, args,
                                     refresh=refresh, wait=False)
        success = True
        return JsonResponse(cache_entry.to_dict())

    finally:
        signals.search.send('hoover.async_search', **{
            'request': request,
            'collections': collections,
            'duration': time() - t0,
            'success': success,
        })


@tracer.wrap_function()
@csrf_exempt
@never_cache
@ratelimit(key='user', rate=rates, block=True)
def async_search_get(request, uuid):
    search_result = models.SearchResultCache.objects.get(task_id=uuid)
    assert search_result.user == request.user
    wait = bool(request.GET.get('wait', None))

    if wait and not search_result.date_finished:
        async_result = _search.AsyncResult(task_id=search_result.task_id)
        # wait for the async result to be set
        async_result.get(timeout=SEARCH_SYNC_WAIT_FOR_RESULTS.total_seconds())
        # flush the object that was being modified in the async task
        search_result.refresh_from_db()
        # make sure it's actually got a result, and return it
        assert search_result.result is not None, "search failed!"

    return JsonResponse(search_result.to_dict())


def thumbnail_rate(group, request):
    # thumbnail url looks like this: baseurl/snoop/collections/{collection}/{hash}/thumbnail/200.jpg
    has_thumbnail = re.search(r'^.+/thumbnail/\d{3}.jpg$', request.path)
    if has_thumbnail:
        return settings.HOOVER_RATELIMIT_THUMBNAIL
    if settings.HOOVER_RATELIMIT_USER:
        return (settings.HOOVER_RATELIMIT_USER[0], settings.HOOVER_RATELIMIT_USER[1])
    else:
        return None


# leave caching unset for the loader to decide
@tracer.wrap_function()
@ratelimit(key='user', rate=thumbnail_rate, block=True)
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


@tracer.wrap_function()
@csrf_exempt
@never_cache
@ratelimit(key='user', rate=rates, block=True)
def doc_tags(request, collection_name, id, suffix):
    for collection in Collection.objects_for_user(request.user):
        if collection.name == collection_name:
            break
    else:
        raise Http404

    username = request.user.username
    if not username:
        return HttpResponseForbidden()
    user_uuid = request.user.profile.uuid
    assert user_uuid, 'user has no tags profile uuid!'
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


@tracer.wrap_function()
@csrf_exempt
@never_cache
@ratelimit(key='user', rate=rates, block=True)
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
    if len(query_strings) > settings.HOOVER_BATCH_LIMIT:
        return JsonErrorResponse("Too many search queries.")
    kwargs = {
        'collections': [c.name for c in collections],
        'query_strings': query_strings,
        'aggs': aggs,
    }

    success = False
    try:
        res = _cached_batch(
            collections,
            request.user,
            kwargs,
            wait=True,
        ).result
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


@tracer.wrap_function()
@csrf_exempt
@never_cache
@ratelimit(key='user', rate=rates, block=True)
def async_batch(request):
    t0 = time()
    body = json.loads(request.body.decode('utf-8'))
    collections = collections_acl(request.user, body['collections'])
    query_strings = body.get('query_strings')
    aggs = body.get('aggs')
    if not collections:
        return JsonErrorResponse("No collections selected.")
    if not query_strings:
        return JsonErrorResponse("No items to be searched.")
    if len(query_strings) > settings.HOOVER_BATCH_LIMIT:
        return JsonErrorResponse("Too many search queries.")
    kwargs = {
        'collections': [c.name for c in collections],
        'query_strings': query_strings,
        'aggs': aggs,
    }

    success = False
    try:
        res = _cached_batch(
            collections,
            request.user,
            kwargs,
            wait=False,
        )
        res['status'] = 'ok'
        success = True
        return JsonResponse(res)

    except es.SearchError as e:
        return JsonErrorResponse(e.reason)

    finally:
        signals.batch.send('hoover.async_batch', **{
            'request': request,
            'collections': collections,
            'duration': time() - t0,
            'success': success,
            'query_count': len(query_strings),
        })


@tracer.wrap_function()
@csrf_exempt
@never_cache
@ratelimit(key='user', rate=rates, block=True)
def async_batch_get(request, uuid):
    batch_result = models.BatchResultCache.objects.get(task_id=uuid)
    assert batch_result.user == request.user
    wait = bool(request.GET.get('wait', None))

    if wait and not batch_result.date_finished:
        async_result = _batch.AsyncResult(task_id=batch_result.task_id)
        # wait for the async result to be set
        async_result.get(timeout=SEARCH_SYNC_WAIT_FOR_RESULTS.total_seconds())
        # flush the object that was being modified in the async task
        batch_result.refresh_from_db()
        # make sure it's actually got a result, and return it
        assert batch_result.result is not None, "batch search failed!"

    return JsonResponse(batch_result.to_dict())


# ================================================================================
#                  ASYNC SEARCH HELPERS
# ================================================================================


def _get_modified_at(collections):
    assert collections
    ts = max(c.get_modified_at()['modified_at'] for c in collections)
    ts = datetime.datetime.fromtimestamp(ts)
    if not timezone.is_aware(ts):
        ts = timezone.make_aware(ts, datetime.timezone.utc)
    return ts


@tracer.wrap_function()
def _cached_batch(collections, user, kwargs, wait=True):
    assert collections
    all_q = models.BatchResultCache.objects.filter(
        user=user,
        args=kwargs,
        date_created__gt=timezone.now() - BATCH_CACHE_AGE,
    )
    # if we have existing hit, check for new collection data
    if all_q.exists():
        all_q = all_q.filter(
            date_created__gt=_get_modified_at(collections),
        )
    # find some existing entry and return it instantly
    found = all_q.filter(result__isnull=False).exists()
    if found:
        cache_entry = all_q.filter(result__isnull=False).order_by('-date_finished')[:1].get()
        log.warn('batch search cache hit: %s', cache_entry)
        return cache_entry
    log.debug('batch search cache miss')
    recent_running_q = all_q.filter(
        result__isnull=True,
        date_created__gt=timezone.now() - BATCH_CACHE_JOIN_RUNNING_MAX_AGE,
    ).order_by('-date_created')
    if recent_running_q.exists():
        cache_entry = recent_running_q[:1].get()
        async_result = _batch.AsyncResult(task_id=cache_entry.task_id)
        log.warning('batch cache hit existing (running): %s', cache_entry)
    else:
        # since we found nothing, create a new entry and launch it
        cache_entry = models.BatchResultCache(user=user, args=kwargs)
        cache_entry.save()
        cache_entry.collections.add(*list(collections))
        cache_entry.save()
        async_result = _batch.apply_async(
            args=(settings.DEBUG_WAIT_PER_COLLECTION, ),
            task_id=cache_entry.task_id,
            kwargs=kwargs,
            queue=BATCH_KEY,
            routing_key=BATCH_KEY,
        )

    if wait:
        # wait for the async result to be set
        async_result.get(timeout=BATCH_SYNC_WAIT_FOR_RESULTS.total_seconds())
        # flush the object that was being modified in the async task
        cache_entry.refresh_from_db()
        # make sure it's actually got a result, and return it
        assert cache_entry.result is not None, "search failed!"

    return cache_entry


@tracer.wrap_function()
def _cached_search(collections, user, kwargs, refresh=False, wait=True):
    assert collections
    # queryset with all valid cache objects for this search
    all_q = models.SearchResultCache.objects.filter(
        user=user, args=kwargs,
        date_created__gt=timezone.now() - SEARCH_CACHE_AGE,
    )
    # if we have existing hit, check for new collection data
    if all_q.exists():
        all_q = all_q.filter(
            date_created__gt=_get_modified_at(collections),
        )
    if not refresh:
        # find some existing entry and return it instantly
        found = all_q.filter(result__isnull=False).exists()
        if found:
            cache_entry = all_q.filter(result__isnull=False).order_by('-date_finished')[:1].get()
            log.warn('search cache hit: %s', cache_entry)
            return cache_entry
        log.debug('search cache miss')
    else:
        log.debug('search cache refresh')

    # since there's no cache hit, find some running entry created less than 2min ago
    recent_running_q = all_q.filter(
        result__isnull=True,
        date_created__gt=timezone.now() - SEARCH_CACHE_JOIN_RUNNING_MAX_AGE,
    ).order_by('-date_created')
    if not refresh and recent_running_q.exists():
        cache_entry = recent_running_q[:1].get()
        async_result = _search.AsyncResult(task_id=cache_entry.task_id)
        log.warning('search cache hit existing (running): %s', cache_entry)
    else:
        # since we found nothing, create a new entry and launch it
        cache_entry = models.SearchResultCache(user=user, args=kwargs)
        cache_entry.save()
        cache_entry.collections.add(*list(collections))
        cache_entry.save()
        async_result = _search.apply_async(
            args=(settings.DEBUG_WAIT_PER_COLLECTION, ),
            task_id=cache_entry.task_id,
            kwargs=kwargs,
            queue=SEARCH_KEY,
            routing_key=SEARCH_KEY,
        )

    if wait:
        # wait for the async result to be set
        async_result.get(timeout=SEARCH_SYNC_WAIT_FOR_RESULTS.total_seconds())
        # flush the object that was being modified in the async task
        cache_entry.refresh_from_db()
        # make sure it's actually got a result, and return it
        assert cache_entry.result is not None, "search failed!"

    return cache_entry


@cel.app.task(bind=True, serializer='json', name=BATCH_KEY, routing_key=BATCH_KEY)
@tracer.wrap_function()
def _batch(self, *args, **kwargs):
    """Background task that actually runs the batch count search through elasticsearch.

    The result is stored in the `BatchResultCache` table as it becomes available.
    """
    try:
        cache = models.BatchResultCache.objects.get(task_id=self.request.id)
        cache.date_started = timezone.now()
        cache.save()
        try:
            res = es.batch_count(**kwargs)
            res['status'] = 'ok'
        except es.SearchError as e:
            return JsonErrorResponse(e.reason)
        cache.result = res
        cache.date_finished = timezone.now()
        cache.save()
        return True
    except Exception as e:
        log.error('_batch celery task execution failed!')
        log.exception(e)
        raise


def _fix_field_type_for_legacy_items(source):
    """Fix for EIC-1201. Index entries created by legacy versions
    have "path" and "filename" as string instead of list of
    strings. This causes grief in the front-end."""
    for key in ["path", "filename"]:
        if isinstance(source.get(key), str):
            source[key] = [source[key]]


@cel.app.task(bind=True, serializer='json', name=SEARCH_KEY, routing_key=SEARCH_KEY)
@tracer.wrap_function()
def _search(self, *args, **kwargs):
    """Background task that actually runs the search through elasticsearch and annotates results.

    The result is stored in the `SearchResultCache` table as it becomes available.
    """
    from .es import _index_id

    def col_name(id):
        return Collection.objects.get(id=id).name

    if 'dedup_collections' in kwargs:
        dedup_collections = kwargs.pop('dedup_collections')
    else:
        dedup_collections = []
    try:
        cache = models.SearchResultCache.objects.get(task_id=self.request.id)
        cache.date_started = timezone.now()
        cache.save()

        try:
            res, counts = es.search(**kwargs)
            res['status'] = 'ok'
        except es.SearchError as e:
            return JsonErrorResponse(e.reason)

        dedup_hits = {}
        if dedup_collections:
            dedup_ids = []
            for item in res['hits']['hits']:
                name = col_name(_index_id(item['_index']))
                doc_hash = item['_id']
                dedup_ids.append(doc_hash)
            hits_url = settings.SNOOP_BASE_URL + '/common/collection-hits'
            hits_req = {
                'collection_list': dedup_collections,
                'doc_sha3_list': dedup_ids,
            }
            try:
                dedup_hits = requests.get(hits_url, json=hits_req).json()['hits']
            except Exception as e:
                log.exception(e)
                log.warning('error: could not get hits: %s (see above)', str(e))

        for item in res['hits']['hits']:
            name = col_name(_index_id(item['_index']))
            doc_hash = item['_id']
            url = 'doc/{}/{}'.format(name, doc_hash)
            item['_collection'] = name
            item['_url_rel'] = url
            _doc_hits = dedup_hits.get(doc_hash)
            item['_dedup_hits'] = _doc_hits
            item['_dedup_hide_result'] = (_doc_hits and (name != _doc_hits[0]))

            # EIC-1201 --> fix legacy format where "path" and "filename" were
            # strings and not lists of strings.
            if item.get('_source'):
                _fix_field_type_for_legacy_items(item['_source'])

        res['count_by_index'] = {
            col_name(i): counts[i]
            for i in counts
        }
        res = _sanitize_utf8_values(res)
        cache.result = res
        cache.date_finished = timezone.now()
        cache.save()
        return True
    except Exception as e:
        log.error('_search celery task execution failed!')
        log.exception(e)
        raise


# ================================================================================
#                  ERROR HANDLERS AND LEGACY REDIRECTORS
# ================================================================================

def handler_403(request, exception=None):
    '''Custom 403 error handler.

    Returns a 429 Response if the rate limit is exceeded. In any other case it
    calls the default django 403 handler (permission_denied).
    '''
    if isinstance(exception, Ratelimited):
        return HttpResponse('Too many requests', status=429)
    else:
        return permission_denied(request, exception)


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
