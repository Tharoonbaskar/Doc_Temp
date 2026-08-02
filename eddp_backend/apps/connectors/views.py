from apps.common.views import EnterpriseServiceViewSet

from .serializers import ConnectorSerializer
from .services import ConnectorService


class ConnectorViewSet(EnterpriseServiceViewSet):
	service_class = ConnectorService
	serializer_class = ConnectorSerializer
