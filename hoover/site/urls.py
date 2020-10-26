from django.conf import settings
from django.urls import include, path, re_path
from ..search.admin import admin_site
from ..search import views, ui
from ..contrib import installed

urlpatterns = [
    path('admin/', admin_site.urls),
    path('api/v0/_ping', views.ping, name='ping'),
    path('api/v0/_is_staff', views.is_staff),
    path('api/v0/search', views.search, name='search'),
    path('api/v0/whoami', views.whoami, name='whoami'),
    path('api/v0/batch', views.batch, name='batch'),
    path('api/v0/limits', views.limits, name='limits'),
    path('api/v0/collections', views.collections, name='collections'),
    re_path(r'^api/v0/doc/(?P<collection_name>[^/]+)/(?P<id>[^/]+)(?P<suffix>.*)$', views.doc),
]

if installed.twofactor:
    assert not installed.oauth2, \
        "hoover.contrib.twofactor and hoover.contrib.oauth2 are not compatible"
    from ..contrib.twofactor import views as twofactor_views
    from django.contrib.auth import views as auth_views
    login_view = auth_views.LoginView.as_view(
        authentication_form=twofactor_views.AuthenticationForm,
    )
    urlpatterns += [
        path('invitation/<code>', twofactor_views.invitation),
        path('accounts/login/', login_view),
        path('accounts/', include('django.contrib.auth.urls')),
    ]

elif installed.oauth2:
    from ..contrib.oauth2 import views as oauth2_views
    urlpatterns += [
        path('accounts/login/', oauth2_views.oauth2_login),
        path('accounts/oauth2-exchange/', oauth2_views.oauth2_exchange),
        path('accounts/logout/', oauth2_views.oauth2_logout, name='logout'),
    ]

else:
    urlpatterns += [
        path('accounts/', include('django.contrib.auth.urls')),
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
