"""
URL configuration for config project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import include, path, re_path
from django.conf import settings
from django.conf.urls.static import static
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularSwaggerView,
    SpectacularRedocView,
)

from apps.connectors.views import ConnectorViewSet
from apps.documents.views import DocumentDefinitionViewSet, DocumentViewSet
from apps.identity.views import PermissionViewSet
from apps.templates.views import TemplateRenderAPIView, TemplateVersionViewSet, TemplateViewSet
from apps.variables.views import VariableViewSet


def _build_viewset_aliases(viewset_class):
    return {
        "list": viewset_class.as_view({"get": "list", "post": "create"}),
        "detail": viewset_class.as_view(
            {
                "get": "retrieve",
                "put": "update",
                "patch": "partial_update",
                "delete": "destroy",
            }
        ),
        "restore": viewset_class.as_view({"post": "restore"}),
        "exists": viewset_class.as_view({"get": "exists"}),
    }


document_alias = _build_viewset_aliases(DocumentViewSet)
template_alias = _build_viewset_aliases(TemplateViewSet)
variable_alias = _build_viewset_aliases(VariableViewSet)
connector_alias = _build_viewset_aliases(ConnectorViewSet)
document_definition_alias = _build_viewset_aliases(DocumentDefinitionViewSet)
template_version_alias = _build_viewset_aliases(TemplateVersionViewSet)
permission_alias = _build_viewset_aliases(PermissionViewSet)

urlpatterns = [
    # Django Admin
    path('admin/', admin.site.urls),

    # Authentication
    path('api/auth/', include('apps.identity.auth_urls')),

    # Enterprise template rendering endpoint
    re_path(r'^api/v1/templates/render/?$', TemplateRenderAPIView.as_view(), name='template-render-v1'),

    # Phase 1 compatibility aliases (new endpoint names + flattened resources)
    re_path(r'^api/documents/?$', document_alias['list'], name='document-alias-list'),
    re_path(r'^api/documents/exists/?$', document_alias['exists'], name='document-alias-exists'),
    re_path(r'^api/documents/(?P<pk>[0-9a-fA-F-]+)/restore/?$', document_alias['restore'], name='document-alias-restore'),
    re_path(r'^api/documents/(?P<pk>[0-9a-fA-F-]+)/?$', document_alias['detail'], name='document-alias-detail'),

    re_path(r'^api/templates/?$', template_alias['list'], name='template-alias-list'),
    re_path(r'^api/templates/exists/?$', template_alias['exists'], name='template-alias-exists'),
    re_path(r'^api/templates/(?P<pk>[0-9a-fA-F-]+)/restore/?$', template_alias['restore'], name='template-alias-restore'),
    re_path(r'^api/templates/(?P<pk>[0-9a-fA-F-]+)/?$', template_alias['detail'], name='template-alias-detail'),

    re_path(r'^api/variables/?$', variable_alias['list'], name='variable-alias-list'),
    re_path(r'^api/variables/exists/?$', variable_alias['exists'], name='variable-alias-exists'),
    re_path(r'^api/variables/(?P<pk>[0-9a-fA-F-]+)/restore/?$', variable_alias['restore'], name='variable-alias-restore'),
    re_path(r'^api/variables/(?P<pk>[0-9a-fA-F-]+)/?$', variable_alias['detail'], name='variable-alias-detail'),

    re_path(r'^api/connectors/?$', connector_alias['list'], name='connector-alias-list'),
    re_path(r'^api/connectors/exists/?$', connector_alias['exists'], name='connector-alias-exists'),
    re_path(r'^api/connectors/(?P<pk>[0-9a-fA-F-]+)/restore/?$', connector_alias['restore'], name='connector-alias-restore'),
    re_path(r'^api/connectors/(?P<pk>[0-9a-fA-F-]+)/?$', connector_alias['detail'], name='connector-alias-detail'),

    re_path(r'^api/document-definitions/?$', document_definition_alias['list'], name='document-definition-alias-list'),
    re_path(r'^api/document-definitions/exists/?$', document_definition_alias['exists'], name='document-definition-alias-exists'),
    re_path(r'^api/document-definitions/(?P<pk>[0-9a-fA-F-]+)/restore/?$', document_definition_alias['restore'], name='document-definition-alias-restore'),
    re_path(r'^api/document-definitions/(?P<pk>[0-9a-fA-F-]+)/?$', document_definition_alias['detail'], name='document-definition-alias-detail'),

    re_path(r'^api/template-versions/?$', template_version_alias['list'], name='template-version-alias-list'),
    re_path(r'^api/template-versions/exists/?$', template_version_alias['exists'], name='template-version-alias-exists'),
    re_path(r'^api/template-versions/(?P<pk>[0-9a-fA-F-]+)/restore/?$', template_version_alias['restore'], name='template-version-alias-restore'),
    re_path(r'^api/template-versions/(?P<pk>[0-9a-fA-F-]+)/?$', template_version_alias['detail'], name='template-version-alias-detail'),

    re_path(r'^api/permissions/?$', permission_alias['list'], name='permission-alias-list'),
    re_path(r'^api/permissions/exists/?$', permission_alias['exists'], name='permission-alias-exists'),
    re_path(r'^api/permissions/(?P<pk>[0-9a-fA-F-]+)/restore/?$', permission_alias['restore'], name='permission-alias-restore'),
    re_path(r'^api/permissions/(?P<pk>[0-9a-fA-F-]+)/?$', permission_alias['detail'], name='permission-alias-detail'),

    # App APIs
    path('api/common/', include('apps.common.urls')),
    path('api/identity/', include('apps.identity.urls')),
    path('api/documents/', include('apps.documents.urls')),
    path('api/templates/', include('apps.templates.urls')),
    path('api/variables/', include('apps.variables.urls')),
    path('api/connectors/', include('apps.connectors.urls')),
    
    # API Schema and Documentation
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
]

# Media files serving (development only)
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
