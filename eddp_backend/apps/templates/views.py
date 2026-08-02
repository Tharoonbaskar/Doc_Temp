from rest_framework.decorators import action
from rest_framework import status
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.authentication import JWTAuthentication

from apps.common.views import EnterpriseServiceViewSet
from apps.common.responses import success_response, error_response
from apps.common.permissions import IsAuthenticatedUser

from .serializers import (
	TemplateSerializer, 
	TemplateVersionSerializer,
	TemplateSendForReviewSerializer,
	TemplateApprovalSerializer,
	TemplateSendBackSerializer,
	TemplatePDFRequestSerializer,
	TemplateRenderRequestSerializer,
)
from .services import TemplateService, TemplateVersionService
from .pdf_service import TemplatePDFService
from .render_services import TemplateRenderService
from .models import TemplateVersion


class TemplateViewSet(EnterpriseServiceViewSet):
	service_class = TemplateService
	serializer_class = TemplateSerializer
	
	def update(self, request, pk=None):
		"""Override update to inject user into payload for version creation."""
		def handler():
			# Get validated payload from serializer
			model_cls = self.get_serializer_class().Meta.model
			model_instance = model_cls.all_objects.filter(pk=pk).first()
			if model_instance is None:
				payload = self._validated_payload()
			else:
				payload = self._validated_payload_for_instance(model_instance)
			
			# Add the current user to the payload
			payload['updated_by'] = request.user
			
			# Call service update method
			return self.get_service().update(pk, payload)
		
		return self._run_service_call(handler)
	
	def partial_update(self, request, pk=None):
		"""Override partial_update to inject user into payload for version creation."""
		def handler():
			model_cls = self.get_serializer_class().Meta.model
			model_instance = model_cls.all_objects.filter(pk=pk).first()
			if model_instance is None:
				payload = self._validated_payload(partial=True)
			else:
				payload = self._validated_payload_for_instance(model_instance, partial=True)
			
			# Add the current user to the payload
			payload['updated_by'] = request.user
			
			# Call service update method
			return self.get_service().update(pk, payload)
		
		return self._run_service_call(handler)
	
	@action(detail=True, methods=["get"], url_path="versions")
	def get_versions(self, request, pk=None):
		"""Get all versions for a template."""
		service = self.get_service()
		template = service._get_instance_or_raise(pk)
		
		versions = TemplateVersion.objects.filter(template=template).order_by('-version_number')
		serializer = TemplateVersionSerializer(versions, many=True)
		
		return success_response(
			data=serializer.data,
			message="Versions retrieved successfully.",
			status_code=status.HTTP_200_OK,
		)
	
	@action(detail=True, methods=["post"], url_path="send-for-review")
	def send_for_review(self, request, pk=None):
		"""Send template for review/approval."""
		serializer = TemplateSendForReviewSerializer(data=request.data)
		serializer.is_valid(raise_exception=True)
		
		service = self.get_service()
		result = service.send_for_review(pk, request.user)
		
		return success_response(
			data=TemplateSerializer(result).data,
			message="Template sent for review successfully.",
			status_code=status.HTTP_200_OK,
		)
	
	@action(detail=True, methods=["post"], url_path="approve")
	def approve(self, request, pk=None):
		"""Approve template with effective date."""
		serializer = TemplateApprovalSerializer(data=request.data)
		serializer.is_valid(raise_exception=True)
		
		service = self.get_service()
		result = service.approve_template(
			pk, 
			request.user,
			serializer.validated_data.get("effective_date"),
			serializer.validated_data.get("review_comments", "")
		)
		
		return success_response(
			data=TemplateSerializer(result).data,
			message="Template approved successfully.",
			status_code=status.HTTP_200_OK,
		)
	
	@action(detail=True, methods=["post"], url_path="send-back")
	def send_back(self, request, pk=None):
		"""Send template back to draft for revision."""
		serializer = TemplateSendBackSerializer(data=request.data)
		serializer.is_valid(raise_exception=True)
		
		service = self.get_service()
		result = service.send_back_for_revision(
			pk, 
			request.user,
			serializer.validated_data.get("comments", "")
		)
		
		return success_response(
			data=TemplateSerializer(result).data,
			message="Template sent back for revision.",
			status_code=status.HTTP_200_OK,
		)
	
	@action(detail=False, methods=["post"], url_path="parse-word-document", parser_classes=[MultiPartParser, FormParser])
	def parse_word_document(self, request):
		"""Parse uploaded Word document and return enterprise import payload."""
		file = request.FILES.get('file')
		
		if not file:
			return error_response(
				message="No file uploaded.",
				status_code=status.HTTP_400_BAD_REQUEST,
			)
		
		if not file.name.endswith('.docx'):
			return error_response(
				message="Only .docx files are supported.",
				status_code=status.HTTP_400_BAD_REQUEST,
			)
		
		try:
			from .parsers import ProseMirrorDocumentParser
			parser = ProseMirrorDocumentParser()
			parsed_payload = parser.parse(file)
			
			return success_response(
				data=parsed_payload,
				message="Word document parsed successfully.",
				status_code=status.HTTP_200_OK,
			)
		except Exception as e:
			return error_response(
				message=f"Failed to parse Word document: {str(e)}",
				status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
			)
	
	@action(detail=True, methods=["get"], url_path="versions/(?P<version_number>[0-9]+)/changes")
	def get_version_changes(self, request, pk=None, version_number=None):
		"""Get version changes with element-level diff details."""
		service = self.get_service()
		response = service.get_version_changes(pk, int(version_number))
		return response

	@action(detail=True, methods=["get"], url_path="versions/(?P<version_number>[0-9]+)")
	def get_version_detail(self, request, pk=None, version_number=None):
		"""Get full version detail for draft editor/review workspace."""
		service = self.get_service()
		response = service.get_version_detail(pk, int(version_number))
		return response

	@action(detail=True, methods=["put"], url_path="versions/(?P<version_number>[0-9]+)/edit")
	def update_draft_version(self, request, pk=None, version_number=None):
		"""Update draft version using ProseMirror JSON and regenerate diff changes."""
		service = self.get_service()
		new_content_payload = request.data.get('prosemirror_json')
		if new_content_payload is None:
			return error_response(
				message="prosemirror_json is required.",
				status_code=status.HTTP_400_BAD_REQUEST,
			)

		page_size = request.data.get('page_size')
		page_orientation = request.data.get('page_orientation')

		if isinstance(new_content_payload, dict):
			if isinstance(page_size, str) and page_size.strip():
				new_content_payload['page_size'] = page_size
			if isinstance(page_orientation, str) and page_orientation.strip():
				new_content_payload['page_orientation'] = page_orientation

		response = service.update_draft_version(pk, int(version_number), request.user, new_content_payload)
		return response

	@action(detail=True, methods=["post"], url_path="versions/(?P<version_number>[0-9]+)/send-for-review")
	def send_draft_version_for_review(self, request, pk=None, version_number=None):
		"""Send draft version for review."""
		service = self.get_service()
		response = service.send_draft_version_for_review(pk, int(version_number), request.user)
		return response
	
	@action(detail=True, methods=["post"], url_path="versions/(?P<version_number>[0-9]+)/approve")
	def approve_draft_version(self, request, pk=None, version_number=None):
		"""Approve a draft version after all changes are reviewed."""
		service = self.get_service()
		response = service.approve_draft_version(pk, int(version_number), request.user)
		return response

	@action(detail=True, methods=["delete"], url_path="versions/(?P<version_number>[0-9]+)/discard")
	def delete_draft_version(self, request, pk=None, version_number=None):
		"""Delete a pending draft/in-review version."""
		service = self.get_service()
		response = service.delete_draft_version(pk, int(version_number), request.user)
		return response
	
	@action(detail=False, methods=["post"], url_path="changes/(?P<change_id>[^/.]+)/review")
	def review_element_change(self, request, change_id=None):
		"""Review (approve/reject) a single element change."""
		action_type = request.data.get('action')
		comment = request.data.get('comment', '')
		
		if not action_type:
			return error_response(
				message="Action is required (APPROVED, REJECTED, REVERTED, SENT_BACK, RESOLVED, or PENDING).",
				status_code=status.HTTP_400_BAD_REQUEST,
			)
		
		service = self.get_service()
		response = service.review_element_change(change_id, request.user, action_type, comment)
		return response

	@action(detail=True, methods=["post"], url_path="preview-pdf")
	def preview_pdf(self, request, pk=None):
		"""Preview enterprise PDF from approved ProseMirror template version."""
		serializer = TemplatePDFRequestSerializer(data=request.data)
		serializer.is_valid(raise_exception=True)

		service = TemplatePDFService()
		return service.preview_pdf(
			request=request,
			template_id=pk,
			payload=dict(serializer.validated_data),
		)

	@action(detail=True, methods=["post"], url_path="generate-pdf")
	def generate_pdf(self, request, pk=None):
		"""Generate enterprise PDF artifact from approved ProseMirror template version."""
		serializer = TemplatePDFRequestSerializer(data=request.data)
		serializer.is_valid(raise_exception=True)

		service = TemplatePDFService()
		return service.generate_pdf(
			request=request,
			template_id=pk,
			payload=dict(serializer.validated_data),
		)

	@action(detail=True, methods=["get"], url_path="download-pdf")
	def download_pdf(self, request, pk=None):
		"""Download PDF for latest approved template version or a specific approved version."""
		service = TemplatePDFService()
		return service.download_pdf(
			request=request,
			template_id=pk,
			query_params=request.query_params,
		)


class TemplateVersionViewSet(EnterpriseServiceViewSet):
	service_class = TemplateVersionService
	serializer_class = TemplateVersionSerializer


class TemplateRenderAPIView(APIView):
	authentication_classes = []
	permission_classes = [AllowAny]

	def post(self, request, *args, **kwargs) -> Response:
		serializer = TemplateRenderRequestSerializer(data=request.data)
		serializer.is_valid(raise_exception=True)

		validated = serializer.validated_data
		render_service = TemplateRenderService()
		payload, status_code = render_service.render(
			template_code=validated["template_code"],
			payload=validated["payload"],
			output_format=validated["output"]["format"],
			response_type=validated["output"]["response"],
			user=getattr(request, "user", None),
		)

		return Response(payload, status=status_code)
