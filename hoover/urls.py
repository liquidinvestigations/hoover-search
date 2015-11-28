from django.conf.urls import include, url
from django.contrib import admin
from collector.admin import admin_site

urlpatterns = [
    url(r'^admin/', include(admin_site.urls)),
    url(r'^$', 'collector.views.home', name='home'),
    url(r'^search$', 'collector.views.search', name='search'),
    url(r'^accounts/', include('django.contrib.auth.urls')),
]
