from rest_framework.routers import DefaultRouter

from .views import ActivityLogViewSet, AuditLogViewSet, SnapshotViewSet

app_name = "governance"

router = DefaultRouter()
router.register("audit-logs", AuditLogViewSet, basename="audit-log")
router.register("activity-logs", ActivityLogViewSet, basename="activity-log")
router.register("snapshots", SnapshotViewSet, basename="snapshot")

urlpatterns = router.urls
