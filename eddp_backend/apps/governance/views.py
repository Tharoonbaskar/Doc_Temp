from apps.common.views import EnterpriseServiceViewSet

from .serializers import ActivityLogSerializer, AuditLogSerializer, SnapshotSerializer
from .services import ActivityLogService, GovernanceService, SnapshotService


class AuditLogViewSet(EnterpriseServiceViewSet):
	service_class = GovernanceService
	serializer_class = AuditLogSerializer


class ActivityLogViewSet(EnterpriseServiceViewSet):
	service_class = ActivityLogService
	serializer_class = ActivityLogSerializer


class SnapshotViewSet(EnterpriseServiceViewSet):
	service_class = SnapshotService
	serializer_class = SnapshotSerializer
