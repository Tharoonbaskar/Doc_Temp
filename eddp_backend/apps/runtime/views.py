from __future__ import annotations

from drf_spectacular.utils import OpenApiParameter, OpenApiResponse, extend_schema
from rest_framework.views import APIView
from rest_framework_simplejwt.authentication import JWTAuthentication

from apps.common.permissions import IsAuthenticatedUser
from apps.common.views import EnterpriseServiceViewSet

from .serializers import (
	ConnectorExecutionRequestSerializer,
	ConnectorValidationRequestSerializer,
	DOCXGenerationRequestSerializer,
	GenerationRequestSerializer,
	HTMLBuildRequestSerializer,
	PDFGenerationRequestSerializer,
	RuleExecutionRequestSerializer,
	RuntimeGenerateRequestSerializer,
	RuntimePreviewRequestSerializer,
	TemplateRenderRequestSerializer,
	VariableResolutionRequestSerializer,
)
from .services import GenerationService, RuntimeService


class GenerationRequestViewSet(EnterpriseServiceViewSet):
	service_class = RuntimeService
	serializer_class = GenerationRequestSerializer


class VariableResolutionAPIView(APIView):
	authentication_classes = [JWTAuthentication]
	permission_classes = [IsAuthenticatedUser]

	@extend_schema(
		request=VariableResolutionRequestSerializer,
		responses={200: OpenApiResponse(description="Variables resolved successfully")},
		tags=["Runtime"],
	)
	def post(self, request, *args, **kwargs):
		serializer = VariableResolutionRequestSerializer(data=request.data)
		serializer.is_valid(raise_exception=True)
		service = RuntimeService()
		return service.resolve_variables(dict(serializer.validated_data))


class RuleExecutionAPIView(APIView):
	authentication_classes = [JWTAuthentication]
	permission_classes = [IsAuthenticatedUser]

	@extend_schema(
		request=RuleExecutionRequestSerializer,
		responses={200: OpenApiResponse(description="Rules executed successfully")},
		tags=["Runtime"],
	)
	def post(self, request, *args, **kwargs):
		serializer = RuleExecutionRequestSerializer(data=request.data)
		serializer.is_valid(raise_exception=True)
		service = RuntimeService()
		return service.execute_rules(dict(serializer.validated_data))


class ConnectorExecutionAPIView(APIView):
	authentication_classes = [JWTAuthentication]
	permission_classes = [IsAuthenticatedUser]

	@extend_schema(
		request=ConnectorExecutionRequestSerializer,
		responses={200: OpenApiResponse(description="Connector executed successfully")},
		tags=["Runtime"],
	)
	def post(self, request, *args, **kwargs):
		serializer = ConnectorExecutionRequestSerializer(data=request.data)
		serializer.is_valid(raise_exception=True)
		service = RuntimeService()
		return service.execute_connector(dict(serializer.validated_data))


class ConnectorValidationAPIView(APIView):
	authentication_classes = [JWTAuthentication]
	permission_classes = [IsAuthenticatedUser]

	@extend_schema(
		request=ConnectorValidationRequestSerializer,
		responses={200: OpenApiResponse(description="Connector validation completed")},
		tags=["Runtime"],
	)
	def post(self, request, *args, **kwargs):
		serializer = ConnectorValidationRequestSerializer(data=request.data)
		serializer.is_valid(raise_exception=True)
		service = RuntimeService()
		return service.validate_connector(dict(serializer.validated_data))


class TemplateRenderingAPIView(APIView):
	authentication_classes = [JWTAuthentication]
	permission_classes = [IsAuthenticatedUser]

	@extend_schema(
		request=TemplateRenderRequestSerializer,
		responses={200: OpenApiResponse(description="Template rendered successfully")},
		tags=["Runtime"],
	)
	def post(self, request, *args, **kwargs):
		serializer = TemplateRenderRequestSerializer(data=request.data)
		serializer.is_valid(raise_exception=True)
		service = RuntimeService()
		return service.render_template(dict(serializer.validated_data))


class HTMLBuildAPIView(APIView):
	authentication_classes = [JWTAuthentication]
	permission_classes = [IsAuthenticatedUser]

	@extend_schema(
		request=HTMLBuildRequestSerializer,
		responses={200: OpenApiResponse(description="HTML built successfully")},
		tags=["Runtime"],
	)
	def post(self, request, *args, **kwargs):
		serializer = HTMLBuildRequestSerializer(data=request.data)
		serializer.is_valid(raise_exception=True)
		service = RuntimeService()
		return service.build_html(dict(serializer.validated_data))


class PDFGenerationAPIView(APIView):
	authentication_classes = [JWTAuthentication]
	permission_classes = [IsAuthenticatedUser]

	@extend_schema(
		request=PDFGenerationRequestSerializer,
		responses={201: OpenApiResponse(description="PDF generated successfully")},
		tags=["Runtime"],
	)
	def post(self, request, *args, **kwargs):
		serializer = PDFGenerationRequestSerializer(data=request.data)
		serializer.is_valid(raise_exception=True)
		service = RuntimeService()
		return service.generate_pdf(dict(serializer.validated_data))


class DOCXGenerationAPIView(APIView):
	authentication_classes = [JWTAuthentication]
	permission_classes = [IsAuthenticatedUser]

	@extend_schema(
		request=DOCXGenerationRequestSerializer,
		responses={201: OpenApiResponse(description="DOCX generated successfully")},
		tags=["Runtime"],
	)
	def post(self, request, *args, **kwargs):
		serializer = DOCXGenerationRequestSerializer(data=request.data)
		serializer.is_valid(raise_exception=True)
		service = RuntimeService()
		return service.generate_docx(dict(serializer.validated_data))


class RuntimePreviewAPIView(APIView):
	authentication_classes = [JWTAuthentication]
	permission_classes = [IsAuthenticatedUser]

	@extend_schema(
		request=RuntimePreviewRequestSerializer,
		responses={200: OpenApiResponse(description="Preview generated successfully")},
		tags=["Runtime"],
	)
	def post(self, request, *args, **kwargs):
		serializer = RuntimePreviewRequestSerializer(data=request.data)
		serializer.is_valid(raise_exception=True)
		service = GenerationService()
		return service.preview_document(request=request, data=dict(serializer.validated_data))


class RuntimeGenerateAPIView(APIView):
	authentication_classes = [JWTAuthentication]
	permission_classes = [IsAuthenticatedUser]

	@extend_schema(
		request=RuntimeGenerateRequestSerializer,
		responses={201: OpenApiResponse(description="Document generated successfully")},
		tags=["Runtime"],
	)
	def post(self, request, *args, **kwargs):
		serializer = RuntimeGenerateRequestSerializer(data=request.data)
		serializer.is_valid(raise_exception=True)
		service = GenerationService()
		return service.generate_document(request=request, data=dict(serializer.validated_data))


class RuntimeStatusAPIView(APIView):
	authentication_classes = [JWTAuthentication]
	permission_classes = [IsAuthenticatedUser]

	@extend_schema(
		parameters=[
			OpenApiParameter(
				name="request_id",
				description="Generation request UUID.",
				required=True,
				type=str,
				location=OpenApiParameter.PATH,
			)
		],
		responses={200: OpenApiResponse(description="Generation status fetched successfully")},
		tags=["Runtime"],
	)
	def get(self, request, request_id, *args, **kwargs):
		service = GenerationService()
		return service.generation_status(request=request, request_id=request_id)


class RuntimeDownloadAPIView(APIView):
	authentication_classes = [JWTAuthentication]
	permission_classes = [IsAuthenticatedUser]

	@extend_schema(
		parameters=[
			OpenApiParameter(
				name="request_id",
				description="Generation request UUID.",
				required=True,
				type=str,
				location=OpenApiParameter.PATH,
			)
		],
		responses={200: OpenApiResponse(description="Download URL generated successfully")},
		tags=["Runtime"],
	)
	def get(self, request, request_id, *args, **kwargs):
		service = GenerationService()
		return service.download_document(request=request, request_id=request_id)


class RuntimeHistoryAPIView(APIView):
	authentication_classes = [JWTAuthentication]
	permission_classes = [IsAuthenticatedUser]

	@extend_schema(
		parameters=[
			OpenApiParameter(
				name="business_reference",
				description="Business reference identifier.",
				required=True,
				type=str,
				location=OpenApiParameter.PATH,
			)
		],
		responses={200: OpenApiResponse(description="Generation history fetched successfully")},
		tags=["Runtime"],
	)
	def get(self, request, business_reference, *args, **kwargs):
		service = GenerationService()
		return service.generation_history(request=request, business_reference=business_reference)
