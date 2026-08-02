from apps.common.views import EnterpriseServiceViewSet

from .serializers import DocumentDefinitionSerializer, DocumentSerializer
from .services import DocumentDefinitionService, DocumentService


class DocumentViewSet(EnterpriseServiceViewSet):
	service_class = DocumentService
	serializer_class = DocumentSerializer


class DocumentDefinitionViewSet(EnterpriseServiceViewSet):
	service_class = DocumentDefinitionService
	serializer_class = DocumentDefinitionSerializer
