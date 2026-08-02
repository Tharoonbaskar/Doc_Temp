from apps.common.views import EnterpriseServiceViewSet

from .serializers import RuleSerializer
from .services import RuleService


class RuleViewSet(EnterpriseServiceViewSet):
	service_class = RuleService
	serializer_class = RuleSerializer
