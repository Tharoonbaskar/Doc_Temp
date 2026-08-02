from apps.common.views import EnterpriseServiceViewSet

from .serializers import VariableSerializer
from .services import VariableService


class VariableViewSet(EnterpriseServiceViewSet):
	service_class = VariableService
	serializer_class = VariableSerializer
