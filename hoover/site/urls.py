from django.conf import settings
from django.conf.urls import include, url
from django.contrib import admin
from ..search.admin import admin_site
from ..search import views, uploads, ui
from ..contrib import installed

urlpatterns = [
    url(r'^_ping$', views.ping, name='ping'),
    url(r'^admin/', include(admin_site.urls)),
    url(r'^search$', views.search, name='search'),
    url(r'^whoami$', views.whoami, name='whoami'),
    url(r'^collections$', views.collections, name='collections'),
    url(r'^(?s)doc/(?P<collection_name>[^/]+)/(?P<id>[^/]+)(?P<suffix>.*)$', views.doc),
]

if installed.twofactor:
    from ..contrib.twofactor import views as twofactor_views
    from django.contrib.auth import views as auth_views
    urlpatterns += [
        url(r'^invitation/(?P<code>.*)$', twofactor_views.invitation),
        url(r'^accounts/login/$', auth_views.login, kwargs={
            'authentication_form': twofactor_views.AuthenticationForm}),
    ]

urlpatterns += [
    url(r'^accounts/', include('django.contrib.auth.urls')),
    url(r'^uploads/(?P<filename>.+)$', uploads.serve_file),
]

if settings.HOOVER_UI_ROOT:
    urlpatterns += [
        url(r'^(?P<filename>.*)$', ui.file),
    ]
else:
    urlpatterns += [
        url(r'^$', views.home, name='home'),
    ]
