from rest_framework.routers import DefaultRouter

from .views import RuleViewSet

app_name = "rules"

router = DefaultRouter()
router.register("rules", RuleViewSet, basename="rule")

urlpatterns = router.urls
