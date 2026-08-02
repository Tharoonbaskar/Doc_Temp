from rest_framework.routers import DefaultRouter

from .views import VariableViewSet

app_name = "variables"

router = DefaultRouter()
router.register("", VariableViewSet, basename="variable")

urlpatterns = router.urls
