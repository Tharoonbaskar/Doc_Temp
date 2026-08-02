from rest_framework.routers import DefaultRouter

from .views import DocumentDefinitionViewSet, DocumentViewSet

app_name = "documents"

router = DefaultRouter()
router.register("", DocumentViewSet, basename="document")
router.register("document-definitions", DocumentDefinitionViewSet, basename="document-definition")

urlpatterns = router.urls
