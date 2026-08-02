from rest_framework.routers import DefaultRouter

from .views import LoanAccountViewSet

router = DefaultRouter()
router.register("loans", LoanAccountViewSet, basename="loan")

urlpatterns = router.urls
