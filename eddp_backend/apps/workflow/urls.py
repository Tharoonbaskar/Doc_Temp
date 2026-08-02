from rest_framework.routers import DefaultRouter

from .views import WorkflowViewSet

app_name = "workflow"

router = DefaultRouter()
router.register("workflows", WorkflowViewSet, basename="workflow")

urlpatterns = router.urls
