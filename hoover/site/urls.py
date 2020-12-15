from django.urls import include, path, re_path
from django.conf import settings
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi

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
    path('search_fields', views.search_fields, name='search_fields'),
    re_path(r'^doc/(?P<collection_name>[^/]+)/(?P<id>[^/]+)/tags/(?P<suffix>.*)$', views.doc_tags),
    re_path(r'^doc/(?P<collection_name>[^/]+)/(?P<id>[^/]+)(?P<suffix>.*)$', views.doc),
]

urlpatterns = [
    path('admin/', admin_site.urls),
    path('accounts/', include('django.contrib.auth.urls')),
    path('api/v0/', include(api_urlpatterns)),
]

# DRF-YASG
# ========
if settings.DEBUG:
    schema_view = get_schema_view(
        openapi.Info(
            title="Search API",
            default_version='v0',
            # description="Liquid API for Tags",
            # contact=openapi.Contact(email="contact@liquiddemo.org"),
            # license=openapi.License(name="MIT License"),
        ),
        public=True,
        permission_classes=[permissions.AllowAny],
        validators=['ssv'],
    )

    schema_urlpatterns = [
        re_path(r'^swagger(?P<format>\.json|\.yaml)$',
                schema_view.without_ui(cache_timeout=0), name='schema-json'),
        re_path(r'^swagger/$', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
        re_path(r'^redoc/$', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
    ]

    urlpatterns += schema_urlpatterns
