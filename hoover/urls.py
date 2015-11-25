from django.conf.urls import include, url
from django.contrib import admin

urlpatterns = [
    url(r'^admin/', include(admin.site.urls)),
    url(r'^$', 'collector.views.home', name='home'),
    url(r'^search$', 'collector.views.search', name='search'),
    url(r'^accounts/', include('django.contrib.auth.urls')),
]
