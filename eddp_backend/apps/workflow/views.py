from apps.common.views import EnterpriseServiceViewSet

from .serializers import WorkflowSerializer
from .services import WorkflowService


class WorkflowViewSet(EnterpriseServiceViewSet):
	service_class = WorkflowService
	serializer_class = WorkflowSerializer
