from rest_framework.routers import DefaultRouter

from .views import ConnectorViewSet

app_name = "connectors"

router = DefaultRouter()
router.register("", ConnectorViewSet, basename="connector")

urlpatterns = router.urls
