from rest_framework.routers import DefaultRouter
from django.urls import path

from .views import TemplateRenderAPIView, TemplateVersionViewSet, TemplateViewSet

app_name = "templates"

router = DefaultRouter()
router.register("templates", TemplateViewSet, basename="template-registry")
router.register("template-versions", TemplateVersionViewSet, basename="template-version")
router.register("", TemplateViewSet, basename="template")

urlpatterns = router.urls
urlpatterns += [
	path("render", TemplateRenderAPIView.as_view(), name="template-render"),
]
