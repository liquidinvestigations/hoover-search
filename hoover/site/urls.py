from django.conf import settings
from django.urls import include, path, re_path
from ..search.admin import admin_site
from ..search import views, ui

# FIXME take /api/v0 routes to separate list, include that under prefix once
urlpatterns = [
    path('admin/', admin_site.urls),
    path('accounts/', include('django.contrib.auth.urls')),
    path('api/v0/_ping', views.ping, name='ping'),
    path('api/v0/_is_staff', views.is_staff),
    path('api/v0/search', views.search, name='search'),
    path('api/v0/whoami', views.whoami, name='whoami'),
    path('api/v0/batch', views.batch, name='batch'),
    path('api/v0/limits', views.limits, name='limits'),
    path('api/v0/collections', views.collections, name='collections'),
    re_path(r'^api/v0/doc/(?P<collection_name>[^/]+)/(?P<id>[^/]+)(?P<suffix>.*)$', views.doc),
]

if settings.HOOVER_UI_BASE_URL:
    urlpatterns += [
        re_path(r'^(?P<path>.*)$', ui.proxy),
        path('', ui.proxy, name='home'),
    ]
else:
    urlpatterns += [
        path('', views.home, name='home'),
    ]
