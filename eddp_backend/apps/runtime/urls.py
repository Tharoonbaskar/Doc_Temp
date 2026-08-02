from django.urls import path
from rest_framework.routers import DefaultRouter

from .views import (
	ConnectorExecutionAPIView,
	ConnectorValidationAPIView,
	DOCXGenerationAPIView,
	GenerationRequestViewSet,
	HTMLBuildAPIView,
	PDFGenerationAPIView,
	RuleExecutionAPIView,
	RuntimeDownloadAPIView,
	RuntimeGenerateAPIView,
	RuntimeHistoryAPIView,
	RuntimePreviewAPIView,
	RuntimeStatusAPIView,
	TemplateRenderingAPIView,
	VariableResolutionAPIView,
)

app_name = "runtime"

router = DefaultRouter()
router.register("generation-requests", GenerationRequestViewSet, basename="generation-request")

urlpatterns = [
	path("resolve-variables", VariableResolutionAPIView.as_view(), name="resolve-variables"),
	path("execute-rules", RuleExecutionAPIView.as_view(), name="execute-rules"),
	path("execute-connector", ConnectorExecutionAPIView.as_view(), name="execute-connector"),
	path("validate-connector", ConnectorValidationAPIView.as_view(), name="validate-connector"),
	path("render-template", TemplateRenderingAPIView.as_view(), name="render-template"),
	path("build-html", HTMLBuildAPIView.as_view(), name="build-html"),
	path("generate-pdf", PDFGenerationAPIView.as_view(), name="generate-pdf"),
	path("generate-docx", DOCXGenerationAPIView.as_view(), name="generate-docx"),
	path("preview", RuntimePreviewAPIView.as_view(), name="preview"),
	path("generate", RuntimeGenerateAPIView.as_view(), name="generate"),
	path("status/<uuid:request_id>", RuntimeStatusAPIView.as_view(), name="status"),
	path("download/<uuid:request_id>", RuntimeDownloadAPIView.as_view(), name="download"),
	path("history/<str:business_reference>", RuntimeHistoryAPIView.as_view(), name="history"),
] + router.urls
