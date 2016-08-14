from django.conf.urls import include, url
from django.contrib import admin
from collector.admin import admin_site
from collector import views, uploads

urlpatterns = [
    url(r'^admin/', include(admin_site.urls)),
    url(r'^$', views.home, name='home'),
    url(r'^search$', views.search, name='search'),
    url(r'^whoami$', views.whoami),
    url(r'^collections$', views.collections, name='collections'),
    url(r'^doc/(?P<collection_name>[^/]+)/(?P<id>.+)$', views.doc),
    url(r'^accounts/', include('django.contrib.auth.urls')),
    url(r'^uploads/(?P<filename>.+)$', uploads.serve_file),
]
