from django.conf.urls import include, url
from django.contrib import admin
from hoover.search.admin import admin_site
from hoover.search import views, uploads

urlpatterns = [
    url(r'^_ping$', views.ping, name='ping'),
    url(r'^admin/', include(admin_site.urls)),
    url(r'^$', views.home, name='home'),
    url(r'^search$', views.search, name='search'),
    url(r'^whoami$', views.whoami),
    url(r'^collections$', views.collections, name='collections'),
    url(r'^(?s)doc/(?P<collection_name>[^/]+)/(?P<id>.+)$', views.doc),
    url(r'^accounts/', include('django.contrib.auth.urls')),
    url(r'^uploads/(?P<filename>.+)$', uploads.serve_file),
]
