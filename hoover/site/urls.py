from django.urls import include, path, re_path
from ..search.admin import admin_site
from ..search import views

api_urlpatterns = [
    path('_ping', views.ping, name='ping'),
    path('_is_staff', views.is_staff),
    path('search', views.search, name='search'),
    path('whoami', views.whoami, name='whoami'),
    path('batch', views.batch, name='batch'),
    path('limits', views.limits, name='limits'),
    path('collections', views.collections, name='collections'),
    re_path(r'^doc/(?P<collection_name>[^/]+)/(?P<id>[^/]+)/tags(?P<suffix>.*)$', views.doc_tags),
    re_path(r'^doc/(?P<collection_name>[^/]+)/(?P<id>[^/]+)(?P<suffix>.*)$', views.doc),
]

urlpatterns = [
    path('admin', admin_site.urls),
    path('accounts', include('django.contrib.auth.urls')),
    path('api/v0', include(api_urlpatterns)),
]
