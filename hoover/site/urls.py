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
    url(r'^batch$', views.batch, name='batch'),
    url(r'^collections$', views.collections, name='collections'),
    url(r'^(?s)doc/(?P<collection_name>[^/]+)/(?P<id>[^/]+)(?P<suffix>.*)$', views.doc),
]

if installed.twofactor:
    assert not installed.oauth2, \
        "hoover.contrib.twofactor and hoover.contrib.oauth2 are not compatible"
    from ..contrib.twofactor import views as twofactor_views
    from django.contrib.auth import views as auth_views
    urlpatterns += [
        url(r'^invitation/(?P<code>.*)$', twofactor_views.invitation),
        url(r'^accounts/login/$', auth_views.login, kwargs={
            'authentication_form': twofactor_views.AuthenticationForm}),
        url(r'^accounts/', include('django.contrib.auth.urls')),
    ]

elif installed.oauth2:
    from ..contrib.oauth2 import views as oauth2_views
    urlpatterns += [
        url(r'^accounts/login/$', oauth2_views.oauth2_login),
        url(r'^accounts/oauth2-exchange/$', oauth2_views.oauth2_exchange),
        url(r'^accounts/logout/$', oauth2_views.oauth2_logout, name='logout'),
    ]

else:
    urlpatterns += [
        url(r'^accounts/', include('django.contrib.auth.urls')),
    ]

urlpatterns += [
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
