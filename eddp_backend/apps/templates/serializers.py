from __future__ import annotations

from rest_framework import serializers

from apps.common.serializers import BaseAuditModelSerializer
from apps.documents.models import Document

from .models import Template, TemplateComponent, TemplateStyle, TemplateVersion, TemplateElementChange


class DocumentReferenceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Document
        fields = ("id", "code", "name")


class TemplateNestedSerializer(serializers.ModelSerializer):
    class Meta:
        model = Template
        fields = ("id", "code", "name", "template_type")


class TemplateVersionNestedSerializer(serializers.ModelSerializer):
    class Meta:
        model = TemplateVersion
        fields = ("id", "code", "version_number", "version_name")


class TemplateSerializer(BaseAuditModelSerializer):
    document = DocumentReferenceSerializer(read_only=True)
    document_id = serializers.PrimaryKeyRelatedField(
        source="document",
        queryset=Document.objects.all(),
        write_only=True,
    )
    approved_by_name = serializers.CharField(source="approved_by.username", read_only=True)
    current_version = serializers.IntegerField(read_only=True)
    version_count = serializers.IntegerField(read_only=True)
    pending_draft_version = serializers.IntegerField(read_only=True)
    has_pending_draft = serializers.BooleanField(read_only=True)
    pending_draft_status = serializers.CharField(read_only=True)

    class Meta:
        model = Template
        fields = (
            "id",
            "code",
            "name",
            "description",
            "category",
            "document",
            "document_id",
            "template_type",
            "content_type",
            "prosemirror_json",
            "page_size",
            "page_orientation",
            "is_default",
            "status",
            "current_version",
            "version_count",
            "pending_draft_version",
            "has_pending_draft",
            "pending_draft_status",
            "effective_date",
            "lifecycle_status",
            "approved_by",
            "approved_by_name",
            "approved_at",
            "review_comments",
            "created_at",
            "updated_at",
            "created_by",
            "updated_by",
            "is_deleted",
            "deleted_at",
        )
        read_only_fields = BaseAuditModelSerializer.AUDIT_READONLY_FIELDS + (
            "lifecycle_status", "approved_by", "approved_at", "current_version", "version_count", 
            "pending_draft_version", "has_pending_draft", "pending_draft_status"
        )

    def validate_name(self, value: str) -> str:
        return self.ensure_non_empty(value, "name")

    def validate_category(self, value: str) -> str:
        return self.ensure_non_empty(value, "category")

    def validate_content_type(self, value: str) -> str:
        return self.ensure_non_empty(value, "content_type")

    def validate(self, attrs):
        attrs = super().validate(attrs)
        document = attrs.get("document") or getattr(self.instance, "document", None)
        name = attrs.get("name") or getattr(self.instance, "name", None)

        if document and name:
            queryset = Template.objects.filter(document=document, name=name)
            if self.instance is not None:
                queryset = queryset.exclude(pk=self.instance.pk)
            if queryset.exists():
                raise serializers.ValidationError(
                    {"name": "Template name must be unique within the selected document."}
                )

        return attrs


class TemplateVersionSerializer(BaseAuditModelSerializer):
    template = TemplateNestedSerializer(read_only=True)
    template_id = serializers.PrimaryKeyRelatedField(
        source="template",
        queryset=Template.objects.all(),
        write_only=True,
    )
    base_version_number = serializers.IntegerField(source="base_version.version_number", read_only=True)
    approved_by_name = serializers.CharField(source="approved_by.username", read_only=True)

    class Meta:
        model = TemplateVersion
        fields = (
            "id",
            "code",
            "template",
            "template_id",
            "version_number",
            "version_name",
            "version_status",
            "template_json",
            "change_summary",
            "published_at",
            "base_version",
            "base_version_number",
            "diff_data",
            "approved_by",
            "approved_by_name",
            "approved_at",
            "status",
            "created_at",
            "updated_at",
            "created_by",
            "updated_by",
            "is_deleted",
            "deleted_at",
        )
        read_only_fields = BaseAuditModelSerializer.AUDIT_READONLY_FIELDS + (
            "base_version_number", "approved_by", "approved_by_name", "approved_at", "diff_data"
        )

    def validate_version_number(self, value: int) -> int:
        if value < 1:
            raise serializers.ValidationError("version_number must be greater than zero.")
        return value

    def validate_version_name(self, value: str) -> str:
        return self.ensure_non_empty(value, "version_name")

    def validate_template_json(self, value):
        return self.ensure_json_compatible(value, "template_json")

    def validate(self, attrs):
        attrs = super().validate(attrs)
        template = attrs.get("template") or getattr(self.instance, "template", None)
        version_number = attrs.get("version_number") or getattr(self.instance, "version_number", None)

        if template and version_number is not None:
            queryset = TemplateVersion.all_objects.filter(
                template=template,
                version_number=version_number,
            )
            if self.instance is not None:
                queryset = queryset.exclude(pk=self.instance.pk)
            if queryset.exists():
                raise serializers.ValidationError(
                    {"version_number": "Version number must be unique per template."}
                )

        return attrs


class TemplateComponentSerializer(BaseAuditModelSerializer):
    template_version = TemplateVersionNestedSerializer(read_only=True)
    template_version_id = serializers.PrimaryKeyRelatedField(
        source="template_version",
        queryset=TemplateVersion.objects.all(),
        write_only=True,
    )

    class Meta:
        model = TemplateComponent
        fields = (
            "id",
            "code",
            "template_version",
            "template_version_id",
            "component_name",
            "component_type",
            "display_order",
            "component_json",
            "status",
            "created_at",
            "updated_at",
            "created_by",
            "updated_by",
            "is_deleted",
            "deleted_at",
        )
        read_only_fields = BaseAuditModelSerializer.AUDIT_READONLY_FIELDS

    def validate_component_name(self, value: str) -> str:
        return self.ensure_non_empty(value, "component_name")

    def validate_display_order(self, value: int) -> int:
        if value < 1:
            raise serializers.ValidationError("display_order must be greater than zero.")
        return value

    def validate_component_json(self, value):
        return self.ensure_json_compatible(value, "component_json")

    def validate(self, attrs):
        attrs = super().validate(attrs)
        template_version = attrs.get("template_version") or getattr(self.instance, "template_version", None)
        display_order = attrs.get("display_order") or getattr(self.instance, "display_order", None)

        if template_version and display_order is not None:
            queryset = TemplateComponent.all_objects.filter(
                template_version=template_version,
                display_order=display_order,
            )
            if self.instance is not None:
                queryset = queryset.exclude(pk=self.instance.pk)
            if queryset.exists():
                raise serializers.ValidationError(
                    {"display_order": "display_order must be unique per template version."}
                )

        return attrs


class TemplateStyleSerializer(BaseAuditModelSerializer):
    template_version = TemplateVersionNestedSerializer(read_only=True)
    template_version_id = serializers.PrimaryKeyRelatedField(
        source="template_version",
        queryset=TemplateVersion.objects.all(),
        write_only=True,
    )

    class Meta:
        model = TemplateStyle
        fields = (
            "id",
            "code",
            "template_version",
            "template_version_id",
            "page_size",
            "orientation",
            "margin_top",
            "margin_bottom",
            "margin_left",
            "margin_right",
            "default_font",
            "default_font_size",
            "style_json",
            "status",
            "created_at",
            "updated_at",
            "created_by",
            "updated_by",
            "is_deleted",
            "deleted_at",
        )
        read_only_fields = BaseAuditModelSerializer.AUDIT_READONLY_FIELDS

    def validate_default_font(self, value: str) -> str:
        return self.ensure_non_empty(value, "default_font")

    def validate_default_font_size(self, value: int) -> int:
        if value < 1:
            raise serializers.ValidationError("default_font_size must be greater than zero.")
        return value

    def validate_style_json(self, value):
        return self.ensure_json_compatible(value, "style_json")

    def validate(self, attrs):
        attrs = super().validate(attrs)
        for field_name in ("margin_top", "margin_bottom", "margin_left", "margin_right"):
            value = attrs.get(field_name)
            if value is None and self.instance is not None:
                value = getattr(self.instance, field_name)
            if value is not None and value < 0:
                raise serializers.ValidationError({field_name: "Margin cannot be negative."})
        return attrs


# Approval workflow serializers
class TemplateSendForReviewSerializer(serializers.Serializer):
    """Serializer for sending a template for review."""
    pass


class TemplateApprovalSerializer(serializers.Serializer):
    """Serializer for approving a template."""
    effective_date = serializers.DateTimeField(required=True, help_text="Date when template becomes active")
    review_comments = serializers.CharField(required=False, allow_blank=True, help_text="Approval comments")
    
    def validate_effective_date(self, value):
        from django.utils import timezone
        if value < timezone.now():
            raise serializers.ValidationError("Effective date must be in the future or present.")
        return value


class TemplateSendBackSerializer(serializers.Serializer):
    """Serializer for sending a template back for revision."""
    comments = serializers.CharField(required=False, allow_blank=True, help_text="Reason for sending back")


# Version management serializers
class TemplateElementChangeSerializer(serializers.ModelSerializer):
    """Serializer for template element changes."""
    reviewed_by_name = serializers.CharField(source="reviewed_by.username", read_only=True)
    
    class Meta:
        model = TemplateElementChange
        fields = (
            "id",
            "element_id",
            "change_type",
            "old_value",
            "new_value",
            "approval_status",
            "reviewed_by",
            "reviewed_by_name",
            "reviewed_at",
            "review_comment",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("id", "reviewed_by", "reviewed_by_name", "reviewed_at", "created_at", "updated_at")


class ReviewElementChangeSerializer(serializers.Serializer):
    """Serializer for reviewing an element change."""
    action = serializers.ChoiceField(
        choices=['APPROVED', 'REJECTED', 'REVERTED', 'SENT_BACK', 'RESOLVED', 'PENDING'],
        required=True,
        help_text="Action to take for this change"
    )
    comment = serializers.CharField(
        required=False,
        allow_blank=True,
        help_text="Optional comment about this review decision"
    )


class TemplatePDFOptionsSerializer(serializers.Serializer):
    page_size = serializers.ChoiceField(
        choices=['A4', 'A3', 'LETTER', 'LEGAL'],
        required=False,
    )
    orientation = serializers.ChoiceField(
        choices=['PORTRAIT', 'LANDSCAPE'],
        required=False,
    )
    margin_top_mm = serializers.FloatField(required=False, min_value=0)
    margin_bottom_mm = serializers.FloatField(required=False, min_value=0)
    margin_left_mm = serializers.FloatField(required=False, min_value=0)
    margin_right_mm = serializers.FloatField(required=False, min_value=0)
    header_height_mm = serializers.FloatField(required=False, min_value=0)
    footer_height_mm = serializers.FloatField(required=False, min_value=0)
    resolution_dpi = serializers.IntegerField(required=False, min_value=72, max_value=600)
    watermark = serializers.CharField(required=False, allow_blank=True)
    include_header_footer = serializers.BooleanField(required=False)
    include_page_numbers = serializers.BooleanField(required=False)
    variable_resolution_mode = serializers.ChoiceField(
        choices=['RESOLVE_STRICT', 'KEEP_UNRESOLVED'],
        required=False,
    )
    font_embedding = serializers.BooleanField(required=False)
    font_family = serializers.CharField(required=False, allow_blank=True)
    header_text = serializers.CharField(required=False, allow_blank=True)
    footer_text = serializers.CharField(required=False, allow_blank=True)
    header_html = serializers.CharField(required=False, allow_blank=True)
    footer_html = serializers.CharField(required=False, allow_blank=True)
    preview_unresolved = serializers.BooleanField(required=False)
    font_faces = serializers.JSONField(required=False, default=list)
    security = serializers.JSONField(required=False, default=dict)

    def validate_font_faces(self, value):
        if not isinstance(value, list):
            raise serializers.ValidationError("font_faces must be a JSON array.")
        return value

    def validate_security(self, value):
        if not isinstance(value, dict):
            raise serializers.ValidationError("security must be a JSON object.")
        return value


class TemplatePDFRequestSerializer(serializers.Serializer):
    version = serializers.CharField(required=False, allow_blank=True)
    variables = serializers.JSONField(required=False, default=dict)
    pdf_options = TemplatePDFOptionsSerializer(required=False)
    metadata = serializers.JSONField(required=False, default=dict)
    file_name = serializers.CharField(required=False, allow_blank=True)

    def validate_variables(self, value):
        if not isinstance(value, dict):
            raise serializers.ValidationError("variables must be a JSON object.")
        return value

    def validate_metadata(self, value):
        if not isinstance(value, dict):
            raise serializers.ValidationError("metadata must be a JSON object.")
        return value


class TemplateRenderOutputSerializer(serializers.Serializer):
    format = serializers.CharField(required=True)
    response = serializers.CharField(required=True)

    def validate_format(self, value: str) -> str:
        normalized = str(value or "").strip().lower()
        if normalized != "pdf":
            raise serializers.ValidationError("Only 'pdf' output format is currently supported.")
        return normalized

    def validate_response(self, value: str) -> str:
        normalized = str(value or "").strip().lower()
        if normalized != "base64":
            raise serializers.ValidationError("Only 'base64' response type is currently supported.")
        return normalized


class TemplateRenderRequestSerializer(serializers.Serializer):
    template_code = serializers.CharField(required=False, allow_blank=True)
    template = serializers.JSONField(required=False)
    payload = serializers.JSONField(required=True)
    output = TemplateRenderOutputSerializer(required=True)

    def validate_template_code(self, value: str) -> str:
        normalized = str(value or "").strip().upper()
        if not normalized:
            raise serializers.ValidationError("template_code is required.")
        return normalized

    def validate_payload(self, value):
        if not isinstance(value, dict):
            raise serializers.ValidationError("payload must be a JSON object.")
        return value

    def validate_template(self, value):
        if value is None:
            return {}
        if not isinstance(value, dict):
            raise serializers.ValidationError("template must be a JSON object.")
        return value

    def validate(self, attrs):
        template_code = str(attrs.get("template_code") or "").strip().upper()
        template_obj = attrs.get("template") or {}

        if not template_code and isinstance(template_obj, dict):
            template_code = str(template_obj.get("code") or "").strip().upper()

        if not template_code:
            raise serializers.ValidationError({"template_code": "template_code is required."})

        attrs["template_code"] = template_code
        return attrs
