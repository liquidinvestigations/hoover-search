from django.views.decorators.csrf import csrf_exempt
from ratelimit.decorators import ratelimit
from django.http import JsonResponse


@csrf_exempt
def async_delete_file(request, collection_name, hash):
    """API view that fetches search results.

    All permission checks for users and fields must be handled here. Then, `_cached_search` is called to
    actually run the search and return results.
    """

    t0 = time()
    if not filemanagement_permissions(request.user, collection_name):
        return

    success = False
    try:
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


@cel.app.task(bind=True, serializer='json', name=SEARCH_KEY, routing_key=SEARCH_KEY)
def _delete_file(self, **kwargs):
    """Background task that actually runs the search through elasticsearch and annotates results.
    The result is stored in the `SearchResultCache` table as it becomes available.
    """
    cache = models.SearchResultCache.objects.get(task_id=self.request.id)
    cache.date_started = timezone.now()
    cache.save()
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
            item['_url_rel'] = url
        res['count_by_index'] = {
            col_name(i): counts[i]
            for i in counts
        }
    cache.result = res
    cache.date_finished = timezone.now()
    cache.save()

    return True
