import uuid

from django.conf import settings
from django.db import models

from apps.common.choices import OutputFormatChoices
from apps.common.models import BaseModel
from apps.documents.models import Document
from apps.templates.models import TemplateVersion


class GenerationRequest(BaseModel):
	# NOTE:
	# Reuse BaseModel.status for request lifecycle instead of adding a separate status field:
	# DRAFT -> ACTIVE (Processing) -> PUBLISHED (Completed) -> ARCHIVED (Expired).
	# If runtime-specific states are needed later (QUEUED/PROCESSING/FAILED/COMPLETED),
	# introduce GenerationStatusChoices and migrate semantics without duplicating status fields.
	request_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False, db_index=True)
	document = models.ForeignKey(
		Document,
		on_delete=models.PROTECT,
		related_name="generation_requests",
	)
	template_version = models.ForeignKey(
		TemplateVersion,
		on_delete=models.PROTECT,
		related_name="generation_requests",
	)
	request_source = models.CharField(max_length=100, db_index=True)
	business_reference = models.CharField(max_length=255, db_index=True)
	input_payload = models.JSONField(default=dict, blank=True)
	requested_by = models.ForeignKey(
		settings.AUTH_USER_MODEL,
		on_delete=models.SET_NULL,
		null=True,
		blank=True,
		related_name="runtime_generation_requests",
	)
	requested_at = models.DateTimeField(auto_now_add=True, db_index=True)
	completed_at = models.DateTimeField(null=True, blank=True, db_index=True)
	processing_time_ms = models.PositiveBigIntegerField(null=True, blank=True)

	class Meta:
		verbose_name = "Generation Request"
		verbose_name_plural = "Generation Requests"

	def __str__(self):
		return str(self.request_id)


class RuntimeContext(BaseModel):
	generation_request = models.OneToOneField(
		GenerationRequest,
		on_delete=models.CASCADE,
		related_name="runtime_context",
	)
	resolved_variables = models.JSONField(default=dict, blank=True)
	executed_rules = models.JSONField(default=list, blank=True)
	validation_results = models.JSONField(default=dict, blank=True)
	connector_response = models.JSONField(default=dict, blank=True)
	execution_log = models.JSONField(default=list, blank=True)

	class Meta:
		verbose_name = "Runtime Context"
		verbose_name_plural = "Runtime Contexts"

	def __str__(self):
		return f"Context: {self.generation_request.request_id}"


class GeneratedDocument(BaseModel):
	generation_request = models.OneToOneField(
		GenerationRequest,
		on_delete=models.CASCADE,
		related_name="generated_document",
	)
	file_name = models.CharField(max_length=255, db_index=True)
	# TODO:
	# Replace local file path handling with object storage locators and metadata
	# for Azure Blob / S3 / MinIO integration.
	file_path = models.CharField(max_length=1024)
	file_type = models.CharField(
		max_length=50,
		choices=OutputFormatChoices.choices,
		db_index=True,
	)
	file_size = models.PositiveBigIntegerField()
	checksum = models.CharField(max_length=128, db_index=True)
	generated_at = models.DateTimeField(auto_now_add=True, db_index=True)
	expiry_date = models.DateTimeField(null=True, blank=True, db_index=True)

	class Meta:
		verbose_name = "Generated Document"
		verbose_name_plural = "Generated Documents"

	def __str__(self):
		return self.file_name
