from rest_framework.routers import DefaultRouter

from .views import LoanApplicationViewSet

router = DefaultRouter()
router.register("applications", LoanApplicationViewSet, basename="application")

urlpatterns = router.urls
