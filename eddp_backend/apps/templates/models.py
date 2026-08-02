from django.db import models
from django.conf import settings

from apps.common.choices import (
	OrientationChoices, 
	PageSizeChoices, 
	TemplateTypeChoices, 
	LifecycleStatusChoices, 
	TemplateStatusChoices,
	VersionStatusChoices,
	ChangeTypeChoices,
)
from apps.common.models import BaseModel
from apps.documents.models import Document


class Template(BaseModel):
	name = models.CharField(max_length=255, db_index=True)
	description = models.TextField(blank=True)
	# Override status field to use TemplateStatusChoices
	status = models.CharField(
		max_length=20,
		choices=TemplateStatusChoices.choices,
		default=TemplateStatusChoices.DRAFT,
		db_index=True,
	)
	# TODO:
	# Replace with ForeignKey when Template Category master data module is implemented.
	category = models.CharField(max_length=100, db_index=True)
	document = models.ForeignKey(
		Document,
		on_delete=models.PROTECT,
		related_name="templates",
	)
	# TODO:
	# Replace with ForeignKey when Template Type master data module is implemented.
	template_type = models.CharField(
		max_length=100,
		choices=TemplateTypeChoices.choices,
		db_index=True,
	)
	# TODO:
	# Replace with ForeignKey when Content Type master data module is implemented.
	content_type = models.CharField(max_length=100, db_index=True)
	content_json = models.TextField(blank=True, null=True, help_text="DEPRECATED: Composite format. Use prosemirror_json instead.")
	prosemirror_json = models.JSONField(default=dict, blank=True, help_text="ProseMirror document (single source of truth)")
	page_size = models.CharField(max_length=10, default='A4', help_text="Page size for rendering (A4, A3, LETTER, etc.)")
	page_orientation = models.CharField(max_length=10, default='PORTRAIT', help_text="Page orientation (PORTRAIT or LANDSCAPE)")
	is_default = models.BooleanField(default=False, db_index=True)
	# TODO:
	# Only one default template should exist per document.
	# Enforce in TemplateService.
	
	# Approval workflow fields
	effective_date = models.DateTimeField(null=True, blank=True, db_index=True, help_text="Date when template becomes active")
	lifecycle_status = models.CharField(
		max_length=20,
		choices=LifecycleStatusChoices.choices,
		default=LifecycleStatusChoices.INACTIVE,
		db_index=True,
		help_text="Automatically derived from effective date"
	)
	approved_by = models.ForeignKey(
		settings.AUTH_USER_MODEL,
		on_delete=models.SET_NULL,
		null=True,
		blank=True,
		related_name="approved_templates",
		help_text="User who approved the template"
	)
	approved_at = models.DateTimeField(null=True, blank=True, help_text="Timestamp when template was approved")
	review_comments = models.TextField(blank=True, help_text="Comments from reviewer during approval")

	class Meta:
		verbose_name = "Template"
		verbose_name_plural = "Templates"
		constraints = [
			models.UniqueConstraint(
				fields=["document", "name"],
				name="uq_document_template_name",
			)
		]

	def __str__(self):
		return self.name
	
	@property
	def current_version(self):
		"""Get the current approved version number. Draft versions must not replace approved version display."""
		latest_approved = self.versions.filter(
			version_status=VersionStatusChoices.APPROVED
		).order_by('-version_number').first()
		return latest_approved.version_number if latest_approved else 1
	
	@property
	def version_count(self):
		"""Get the total count of approved versions."""
		return self.versions.filter(version_status=VersionStatusChoices.APPROVED).count()
	
	@property
	def pending_draft_version(self):
		"""Get the latest in-progress version number after an approved baseline exists."""
		has_approved_baseline = self.versions.filter(
			version_status=VersionStatusChoices.APPROVED
		).exists()
		if not has_approved_baseline:
			return None

		draft = self.versions.filter(
			version_status__in=[VersionStatusChoices.DRAFT, VersionStatusChoices.FOR_REVIEW]
		).order_by('-version_number').first()
		return draft.version_number if draft else None
	
	@property
	def has_pending_draft(self):
		"""Check if there's a pending draft version."""
		return self.pending_draft_version is not None

	@property
	def pending_draft_status(self):
		"""Get latest in-progress version status (DRAFT/FOR_REVIEW) after approved baseline exists."""
		has_approved_baseline = self.versions.filter(
			version_status=VersionStatusChoices.APPROVED
		).exists()
		if not has_approved_baseline:
			return None

		draft = self.versions.filter(
			version_status__in=[VersionStatusChoices.DRAFT, VersionStatusChoices.FOR_REVIEW]
		).order_by('-version_number').first()
		return draft.version_status if draft else None


class TemplateVersion(BaseModel):
	template = models.ForeignKey(
		Template,
		on_delete=models.CASCADE,
		related_name="versions",
	)
	version_number = models.PositiveIntegerField(db_index=True)
	version_name = models.CharField(max_length=150, db_index=True)
	version_status = models.CharField(
		max_length=20,
		choices=VersionStatusChoices.choices,
		default=VersionStatusChoices.DRAFT,
		db_index=True,
		help_text="Status of this version (DRAFT or APPROVED)"
	)
	template_json = models.JSONField(default=dict, blank=True)
	change_summary = models.TextField(blank=True)
	published_at = models.DateTimeField(null=True, blank=True, db_index=True)
	
	# Version tracking fields
	base_version = models.ForeignKey(
		'self',
		on_delete=models.SET_NULL,
		null=True,
		blank=True,
		related_name='derived_versions',
		help_text="The approved version this draft is based on"
	)
	diff_data = models.JSONField(
		default=dict,
		blank=True,
		help_text="Stores the diff between this version and base_version"
	)
	
	# Approval tracking
	approved_by = models.ForeignKey(
		settings.AUTH_USER_MODEL,
		on_delete=models.SET_NULL,
		null=True,
		blank=True,
		related_name="approved_versions",
		help_text="User who approved this version"
	)
	approved_at = models.DateTimeField(null=True, blank=True, help_text="Timestamp when version was approved")

	class Meta:
		verbose_name = "Template Version"
		verbose_name_plural = "Template Versions"
		constraints = [
			models.UniqueConstraint(
				fields=["template", "version_number"],
				name="uq_template_version_number",
			)
		]

	def __str__(self):
		return f"{self.template.name} v{self.version_number}"


class TemplateElementChange(BaseModel):
	"""Tracks individual element-level changes for granular approval"""
	version = models.ForeignKey(
		TemplateVersion,
		on_delete=models.CASCADE,
		related_name="element_changes",
		help_text="The draft version containing this change"
	)
	element_id = models.CharField(
		max_length=255,
		db_index=True,
		help_text="Unique identifier of the element (from template JSON)"
	)
	change_type = models.CharField(
		max_length=20,
		choices=ChangeTypeChoices.choices,
		db_index=True,
		help_text="Type of change: ADDED, MODIFIED, or DELETED"
	)
	old_value = models.JSONField(
		null=True,
		blank=True,
		help_text="Original element data (null for ADDED)"
	)
	new_value = models.JSONField(
		null=True,
		blank=True,
		help_text="New element data (null for DELETED)"
	)
	approval_status = models.CharField(
		max_length=20,
		choices=[
			('PENDING', 'Pending'),
			('APPROVED', 'Approved'),
			('REJECTED', 'Rejected'),
			('REVERTED', 'Reverted'),
			('SENT_BACK', 'Sent Back'),
			('RESOLVED', 'Resolved'),
		],
		default='PENDING',
		db_index=True,
		help_text="Approval status of this specific change"
	)
	reviewed_by = models.ForeignKey(
		settings.AUTH_USER_MODEL,
		on_delete=models.SET_NULL,
		null=True,
		blank=True,
		related_name="reviewed_changes",
		help_text="User who reviewed this change"
	)
	reviewed_at = models.DateTimeField(
		null=True,
		blank=True,
		help_text="Timestamp when change was reviewed"
	)
	review_comment = models.TextField(
		blank=True,
		help_text="Comment from reviewer about this change"
	)
	
	class Meta:
		verbose_name = "Template Element Change"
		verbose_name_plural = "Template Element Changes"
		indexes = [
			models.Index(fields=['version', 'element_id']),
			models.Index(fields=['version', 'approval_status']),
		]
	
	def __str__(self):
		return f"{self.change_type} - {self.element_id} ({self.version})"


class TemplateComponent(BaseModel):
	template_version = models.ForeignKey(
		TemplateVersion,
		on_delete=models.CASCADE,
		related_name="components",
	)
	component_name = models.CharField(max_length=150, db_index=True)
	# TODO:
	# Replace with ForeignKey when Component Type master data module is implemented.
	component_type = models.CharField(max_length=100, db_index=True)
	display_order = models.PositiveIntegerField(db_index=True)
	component_json = models.JSONField(default=dict, blank=True)

	class Meta:
		verbose_name = "Template Component"
		verbose_name_plural = "Template Components"
		constraints = [
			models.UniqueConstraint(
				fields=["template_version", "display_order"],
				name="uq_template_component_display_order",
			)
		]

	def __str__(self):
		return f"{self.component_name} ({self.template_version})"


class TemplateStyle(BaseModel):
	template_version = models.OneToOneField(
		TemplateVersion,
		on_delete=models.CASCADE,
		related_name="style",
	)
	page_size = models.CharField(
		max_length=50,
		choices=PageSizeChoices.choices,
		default=PageSizeChoices.A4,
		db_index=True,
	)
	orientation = models.CharField(
		max_length=20,
		choices=OrientationChoices.choices,
		default=OrientationChoices.PORTRAIT,
		db_index=True,
	)
	margin_top = models.DecimalField(max_digits=6, decimal_places=2, default=0)
	margin_bottom = models.DecimalField(max_digits=6, decimal_places=2, default=0)
	margin_left = models.DecimalField(max_digits=6, decimal_places=2, default=0)
	margin_right = models.DecimalField(max_digits=6, decimal_places=2, default=0)
	default_font = models.CharField(max_length=100, db_index=True)
	default_font_size = models.PositiveSmallIntegerField(default=12)
	style_json = models.JSONField(default=dict, blank=True)

	class Meta:
		verbose_name = "Template Style"
		verbose_name_plural = "Template Styles"

	def __str__(self):
		return f"Style for {self.template_version}"
