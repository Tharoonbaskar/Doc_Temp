from __future__ import annotations

from django.core.exceptions import ValidationError as DjangoValidationError
from django.contrib.auth import get_user_model
from rest_framework import serializers

from apps.common.choices import OutputFormatChoices
from apps.common.serializers import BaseAuditModelSerializer, UserSummarySerializer
from apps.common.validators import validate_json
from apps.documents.models import Document
from apps.templates.models import TemplateVersion

from .models import GeneratedDocument, GenerationRequest, RuntimeContext


class DocumentReferenceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Document
        fields = ("id", "code", "name")


class TemplateVersionReferenceSerializer(serializers.ModelSerializer):
    class Meta:
        model = TemplateVersion
        fields = ("id", "code", "version_number", "version_name")


class GenerationRequestNestedSerializer(serializers.ModelSerializer):
    correlation_id = serializers.CharField(source="business_reference", read_only=True)

    class Meta:
        model = GenerationRequest
        fields = (
            "id",
            "code",
            "request_id",
            "business_reference",
            "correlation_id",
            "status",
        )


class GenerationRequestSerializer(BaseAuditModelSerializer):
    document = DocumentReferenceSerializer(read_only=True)
    document_id = serializers.PrimaryKeyRelatedField(
        source="document",
        queryset=Document.objects.all(),
        write_only=True,
    )
    template_version = TemplateVersionReferenceSerializer(read_only=True)
    template_version_id = serializers.PrimaryKeyRelatedField(
        source="template_version",
        queryset=TemplateVersion.objects.all(),
        write_only=True,
    )
    requested_by = UserSummarySerializer(read_only=True)
    requested_by_id = serializers.PrimaryKeyRelatedField(
        source="requested_by",
        queryset=get_user_model().objects.all(),
        write_only=True,
        required=False,
        allow_null=True,
    )
    correlation_id = serializers.CharField(required=False, allow_blank=False, write_only=True)

    class Meta:
        model = GenerationRequest
        fields = (
            "id",
            "code",
            "request_id",
            "document",
            "document_id",
            "template_version",
            "template_version_id",
            "request_source",
            "business_reference",
            "correlation_id",
            "input_payload",
            "requested_by",
            "requested_by_id",
            "requested_at",
            "completed_at",
            "processing_time_ms",
            "status",
            "created_at",
            "updated_at",
            "created_by",
            "updated_by",
            "is_deleted",
            "deleted_at",
        )
        read_only_fields = BaseAuditModelSerializer.AUDIT_READONLY_FIELDS + (
            "request_id",
            "requested_at",
        )

    def validate_request_source(self, value: str) -> str:
        return self.ensure_non_empty(value, "request_source")

    def validate_business_reference(self, value: str) -> str:
        return self.ensure_non_empty(value, "business_reference")

    def validate_correlation_id(self, value: str) -> str:
        return self.ensure_non_empty(value, "correlation_id")

    def validate_input_payload(self, value):
        return self.ensure_json_compatible(value, "input_payload")

    def validate_processing_time_ms(self, value):
        if value is not None and value < 0:
            raise serializers.ValidationError("processing_time_ms cannot be negative.")
        return value

    def validate(self, attrs):
        correlation_id = attrs.pop("correlation_id", None)
        if correlation_id:
            business_reference = attrs.get("business_reference")
            if business_reference and business_reference != correlation_id:
                raise serializers.ValidationError(
                    {"correlation_id": "correlation_id must match business_reference when both are provided."}
                )
            attrs["business_reference"] = correlation_id

        attrs = super().validate(attrs)
        requested_at = attrs.get("requested_at") or getattr(self.instance, "requested_at", None)
        completed_at = attrs.get("completed_at")
        if completed_at is None and self.instance is not None:
            completed_at = self.instance.completed_at

        if requested_at and completed_at and completed_at < requested_at:
            raise serializers.ValidationError(
                {"completed_at": "completed_at cannot be earlier than requested_at."}
            )
        return attrs

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation["correlation_id"] = representation.get("business_reference")
        return representation


class RuntimeContextSerializer(BaseAuditModelSerializer):
    generation_request = GenerationRequestNestedSerializer(read_only=True)
    generation_request_id = serializers.PrimaryKeyRelatedField(
        source="generation_request",
        queryset=GenerationRequest.objects.all(),
        write_only=True,
    )

    class Meta:
        model = RuntimeContext
        fields = (
            "id",
            "code",
            "generation_request",
            "generation_request_id",
            "resolved_variables",
            "executed_rules",
            "validation_results",
            "connector_response",
            "execution_log",
            "status",
            "created_at",
            "updated_at",
            "created_by",
            "updated_by",
            "is_deleted",
            "deleted_at",
        )
        read_only_fields = BaseAuditModelSerializer.AUDIT_READONLY_FIELDS

    def validate_resolved_variables(self, value):
        validated = self.ensure_json_compatible(value, "resolved_variables")
        if validated is not None and not isinstance(validated, dict):
            raise serializers.ValidationError("resolved_variables must be a JSON object.")
        return validated

    def validate_executed_rules(self, value):
        validated = self.ensure_json_compatible(value, "executed_rules")
        if validated is not None and not isinstance(validated, list):
            raise serializers.ValidationError("executed_rules must be a JSON array.")
        return validated

    def validate_validation_results(self, value):
        validated = self.ensure_json_compatible(value, "validation_results")
        if validated is not None and not isinstance(validated, dict):
            raise serializers.ValidationError("validation_results must be a JSON object.")
        return validated

    def validate_connector_response(self, value):
        validated = self.ensure_json_compatible(value, "connector_response")
        if validated is not None and not isinstance(validated, dict):
            raise serializers.ValidationError("connector_response must be a JSON object.")
        return validated

    def validate_execution_log(self, value):
        validated = self.ensure_json_compatible(value, "execution_log")
        if validated is not None and not isinstance(validated, list):
            raise serializers.ValidationError("execution_log must be a JSON array.")
        return validated


class GeneratedDocumentSerializer(BaseAuditModelSerializer):
    generation_request = GenerationRequestNestedSerializer(read_only=True)
    generation_request_id = serializers.PrimaryKeyRelatedField(
        source="generation_request",
        queryset=GenerationRequest.objects.all(),
        write_only=True,
    )

    class Meta:
        model = GeneratedDocument
        fields = (
            "id",
            "code",
            "generation_request",
            "generation_request_id",
            "file_name",
            "file_path",
            "file_type",
            "file_size",
            "checksum",
            "generated_at",
            "expiry_date",
            "status",
            "created_at",
            "updated_at",
            "created_by",
            "updated_by",
            "is_deleted",
            "deleted_at",
        )
        read_only_fields = BaseAuditModelSerializer.AUDIT_READONLY_FIELDS + ("generated_at",)

    def validate_file_name(self, value: str) -> str:
        return self.ensure_non_empty(value, "file_name")

    def validate_file_path(self, value: str) -> str:
        return self.ensure_non_empty(value, "file_path")

    def validate_checksum(self, value: str) -> str:
        return self.ensure_non_empty(value, "checksum")

    def validate_file_size(self, value: int) -> int:
        if value < 0:
            raise serializers.ValidationError("file_size cannot be negative.")
        return value

    def validate(self, attrs):
        attrs = super().validate(attrs)
        generated_at = attrs.get("generated_at") or getattr(self.instance, "generated_at", None)
        expiry_date = attrs.get("expiry_date")
        if expiry_date is None and self.instance is not None:
            expiry_date = self.instance.expiry_date

        if generated_at and expiry_date and expiry_date <= generated_at:
            raise serializers.ValidationError(
                {"expiry_date": "expiry_date must be later than generated_at."}
            )
        return attrs


class VariableResolutionRequestSerializer(serializers.Serializer):
    generation_request_id = serializers.UUIDField(required=False)
    variable_group_code = serializers.CharField(required=True)
    runtime_payload = serializers.JSONField(required=True)
    database_values = serializers.JSONField(required=False, default=dict)
    connector_values = serializers.JSONField(required=False, default=dict)
    computed_values = serializers.JSONField(required=False, default=dict)

    def validate_variable_group_code(self, value: str) -> str:
        return value.strip()

    @staticmethod
    def _validated_json(value, field_name: str):
        try:
            return validate_json(value)
        except DjangoValidationError as exc:
            raise serializers.ValidationError(str(exc)) from exc

    def validate_runtime_payload(self, value):
        validated = self._validated_json(value, "runtime_payload")
        if not isinstance(validated, dict):
            raise serializers.ValidationError("runtime_payload must be a JSON object.")
        return validated

    def validate_database_values(self, value):
        validated = self._validated_json(value, "database_values")
        if not isinstance(validated, dict):
            raise serializers.ValidationError("database_values must be a JSON object.")
        return validated

    def validate_connector_values(self, value):
        validated = self._validated_json(value, "connector_values")
        if not isinstance(validated, dict):
            raise serializers.ValidationError("connector_values must be a JSON object.")
        return validated

    def validate_computed_values(self, value):
        validated = self._validated_json(value, "computed_values")
        if not isinstance(validated, dict):
            raise serializers.ValidationError("computed_values must be a JSON object.")
        return validated


class RuleExecutionRequestSerializer(serializers.Serializer):
    generation_request_id = serializers.UUIDField(required=False)
    rule_group_code = serializers.CharField(required=True)
    runtime_context = serializers.JSONField(required=False, default=dict)
    resolved_variables = serializers.JSONField(required=False, default=dict)
    connector_response = serializers.JSONField(required=False, default=dict)
    stop_on_critical_failure = serializers.BooleanField(required=False, default=True)

    def validate_rule_group_code(self, value: str) -> str:
        return value.strip()

    @staticmethod
    def _validated_json(value, field_name: str):
        try:
            return validate_json(value)
        except DjangoValidationError as exc:
            raise serializers.ValidationError(str(exc)) from exc

    def validate_runtime_context(self, value):
        validated = self._validated_json(value, "runtime_context")
        if not isinstance(validated, dict):
            raise serializers.ValidationError("runtime_context must be a JSON object.")
        return validated

    def validate_resolved_variables(self, value):
        validated = self._validated_json(value, "resolved_variables")
        if not isinstance(validated, dict):
            raise serializers.ValidationError("resolved_variables must be a JSON object.")
        return validated

    def validate_connector_response(self, value):
        validated = self._validated_json(value, "connector_response")
        if not isinstance(validated, dict):
            raise serializers.ValidationError("connector_response must be a JSON object.")
        return validated


class ConnectorExecutionRequestSerializer(serializers.Serializer):
    generation_request_id = serializers.UUIDField(required=False)
    connector_code = serializers.CharField(required=True)
    operation = serializers.CharField(required=False, allow_blank=True, default="")
    payload = serializers.JSONField(required=False, default=dict)
    context = serializers.JSONField(required=False, default=dict)
    perform_validation = serializers.BooleanField(required=False, default=True)

    def validate_connector_code(self, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise serializers.ValidationError("connector_code is required.")
        return normalized

    @staticmethod
    def _validated_json(value, field_name: str):
        try:
            return validate_json(value)
        except DjangoValidationError as exc:
            raise serializers.ValidationError(str(exc)) from exc

    def validate_payload(self, value):
        validated = self._validated_json(value, "payload")
        if not isinstance(validated, dict):
            raise serializers.ValidationError("payload must be a JSON object.")
        return validated

    def validate_context(self, value):
        validated = self._validated_json(value, "context")
        if not isinstance(validated, dict):
            raise serializers.ValidationError("context must be a JSON object.")
        return validated


class ConnectorValidationRequestSerializer(serializers.Serializer):
    generation_request_id = serializers.UUIDField(required=False)
    connector_code = serializers.CharField(required=True)
    operation = serializers.CharField(required=False, allow_blank=True, default="")
    payload = serializers.JSONField(required=False, default=dict)

    def validate_connector_code(self, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise serializers.ValidationError("connector_code is required.")
        return normalized

    @staticmethod
    def _validated_json(value, field_name: str):
        try:
            return validate_json(value)
        except DjangoValidationError as exc:
            raise serializers.ValidationError(str(exc)) from exc

    def validate_payload(self, value):
        validated = self._validated_json(value, "payload")
        if not isinstance(validated, dict):
            raise serializers.ValidationError("payload must be a JSON object.")
        return validated


class TemplateRenderRequestSerializer(serializers.Serializer):
    generation_request_id = serializers.UUIDField(required=False)
    template_code = serializers.CharField(required=False, allow_blank=True, default="")
    template_version_code = serializers.CharField(required=False, allow_blank=True, default="")
    template_version_id = serializers.UUIDField(required=False, allow_null=True)
    variables = serializers.JSONField(required=False, default=dict)
    options = serializers.JSONField(required=False, default=dict)

    @staticmethod
    def _validated_json(value, field_name: str):
        try:
            return validate_json(value)
        except DjangoValidationError as exc:
            raise serializers.ValidationError(str(exc)) from exc

    def validate_template_code(self, value: str) -> str:
        return value.strip()

    def validate_template_version_code(self, value: str) -> str:
        return value.strip()

    def validate_variables(self, value):
        validated = self._validated_json(value, "variables")
        if not isinstance(validated, dict):
            raise serializers.ValidationError("variables must be a JSON object.")
        return validated

    def validate_options(self, value):
        validated = self._validated_json(value, "options")
        if not isinstance(validated, dict):
            raise serializers.ValidationError("options must be a JSON object.")
        return validated

    def validate(self, attrs):
        attrs = super().validate(attrs)
        template_code = (attrs.get("template_code") or "").strip()
        template_version_code = (attrs.get("template_version_code") or "").strip()
        template_version_id = attrs.get("template_version_id")
        generation_request_id = attrs.get("generation_request_id")

        if not any([template_code, template_version_code, template_version_id, generation_request_id]):
            raise serializers.ValidationError(
                "Provide template_code, template_version_code, template_version_id, "
                "or generation_request_id."
            )
        return attrs


class HTMLBuildRequestSerializer(serializers.Serializer):
    generation_request_id = serializers.UUIDField(required=False)
    template_code = serializers.CharField(required=False, allow_blank=True, default="")
    template_version_code = serializers.CharField(required=False, allow_blank=True, default="")
    template_version_id = serializers.UUIDField(required=False, allow_null=True)
    variables = serializers.JSONField(required=False, default=dict)
    render_options = serializers.JSONField(required=False, default=dict)
    layout_options = serializers.JSONField(required=False, default=dict)
    style_overrides = serializers.CharField(required=False, allow_blank=True, default="")

    @staticmethod
    def _validated_json(value, field_name: str):
        try:
            return validate_json(value)
        except DjangoValidationError as exc:
            raise serializers.ValidationError(str(exc)) from exc

    def validate_template_code(self, value: str) -> str:
        return value.strip()

    def validate_template_version_code(self, value: str) -> str:
        return value.strip()

    def validate_variables(self, value):
        validated = self._validated_json(value, "variables")
        if not isinstance(validated, dict):
            raise serializers.ValidationError("variables must be a JSON object.")
        return validated

    def validate_render_options(self, value):
        validated = self._validated_json(value, "render_options")
        if not isinstance(validated, dict):
            raise serializers.ValidationError("render_options must be a JSON object.")
        return validated

    def validate_layout_options(self, value):
        validated = self._validated_json(value, "layout_options")
        if not isinstance(validated, dict):
            raise serializers.ValidationError("layout_options must be a JSON object.")
        return validated

    def validate(self, attrs):
        attrs = super().validate(attrs)
        template_code = (attrs.get("template_code") or "").strip()
        template_version_code = (attrs.get("template_version_code") or "").strip()
        template_version_id = attrs.get("template_version_id")
        generation_request_id = attrs.get("generation_request_id")

        if not any([template_code, template_version_code, template_version_id, generation_request_id]):
            raise serializers.ValidationError(
                "Provide template_code, template_version_code, template_version_id, "
                "or generation_request_id."
            )
        return attrs


class PDFGenerationRequestSerializer(serializers.Serializer):
    generation_request_id = serializers.UUIDField(required=True)
    template_code = serializers.CharField(required=False, allow_blank=True, default="")
    template_version_code = serializers.CharField(required=False, allow_blank=True, default="")
    template_version_id = serializers.UUIDField(required=False, allow_null=True)
    variables = serializers.JSONField(required=False, default=dict)
    render_options = serializers.JSONField(required=False, default=dict)
    layout_options = serializers.JSONField(required=False, default=dict)
    style_overrides = serializers.CharField(required=False, allow_blank=True, default="")
    file_name = serializers.CharField(required=False, allow_blank=True, default="")

    @staticmethod
    def _validated_json(value, field_name: str):
        try:
            return validate_json(value)
        except DjangoValidationError as exc:
            raise serializers.ValidationError(str(exc)) from exc

    def validate_template_code(self, value: str) -> str:
        return value.strip()

    def validate_template_version_code(self, value: str) -> str:
        return value.strip()

    def validate_variables(self, value):
        validated = self._validated_json(value, "variables")
        if not isinstance(validated, dict):
            raise serializers.ValidationError("variables must be a JSON object.")
        return validated

    def validate_render_options(self, value):
        validated = self._validated_json(value, "render_options")
        if not isinstance(validated, dict):
            raise serializers.ValidationError("render_options must be a JSON object.")
        return validated

    def validate_layout_options(self, value):
        validated = self._validated_json(value, "layout_options")
        if not isinstance(validated, dict):
            raise serializers.ValidationError("layout_options must be a JSON object.")
        return validated


class DOCXGenerationRequestSerializer(serializers.Serializer):
    generation_request_id = serializers.UUIDField(required=True)
    template_code = serializers.CharField(required=False, allow_blank=True, default="")
    template_version_code = serializers.CharField(required=False, allow_blank=True, default="")
    template_version_id = serializers.UUIDField(required=False, allow_null=True)
    variables = serializers.JSONField(required=False, default=dict)
    render_options = serializers.JSONField(required=False, default=dict)
    layout_options = serializers.JSONField(required=False, default=dict)
    style_overrides = serializers.CharField(required=False, allow_blank=True, default="")
    file_name = serializers.CharField(required=False, allow_blank=True, default="")

    @staticmethod
    def _validated_json(value, field_name: str):
        try:
            return validate_json(value)
        except DjangoValidationError as exc:
            raise serializers.ValidationError(str(exc)) from exc

    def validate_template_code(self, value: str) -> str:
        return value.strip()

    def validate_template_version_code(self, value: str) -> str:
        return value.strip()

    def validate_variables(self, value):
        validated = self._validated_json(value, "variables")
        if not isinstance(validated, dict):
            raise serializers.ValidationError("variables must be a JSON object.")
        return validated

    def validate_render_options(self, value):
        validated = self._validated_json(value, "render_options")
        if not isinstance(validated, dict):
            raise serializers.ValidationError("render_options must be a JSON object.")
        return validated

    def validate_layout_options(self, value):
        validated = self._validated_json(value, "layout_options")
        if not isinstance(validated, dict):
            raise serializers.ValidationError("layout_options must be a JSON object.")
        return validated


class RuntimeConnectorStepSerializer(serializers.Serializer):
    connector_code = serializers.CharField(required=True)
    operation = serializers.CharField(required=False, allow_blank=True, default="")
    payload = serializers.JSONField(required=False, default=dict)
    perform_validation = serializers.BooleanField(required=False, default=True)

    @staticmethod
    def _validated_json(value, field_name: str):
        try:
            return validate_json(value)
        except DjangoValidationError as exc:
            raise serializers.ValidationError(str(exc)) from exc

    def validate_connector_code(self, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise serializers.ValidationError("connector_code is required.")
        return normalized

    def validate_payload(self, value):
        validated = self._validated_json(value, "payload")
        if not isinstance(validated, dict):
            raise serializers.ValidationError("payload must be a JSON object.")
        return validated


class RuntimePreviewRequestSerializer(serializers.Serializer):
    generation_request_id = serializers.UUIDField(required=False, allow_null=True)
    document_id = serializers.UUIDField(required=False, allow_null=True)
    variable_group_code = serializers.CharField(required=False, allow_blank=True, default="")
    rule_group_code = serializers.CharField(required=False, allow_blank=True, default="")
    connector_code = serializers.CharField(required=False, allow_blank=True, default="")
    connector_payload = serializers.JSONField(required=False, default=dict)
    connectors = RuntimeConnectorStepSerializer(required=False, many=True, default=list)

    template_code = serializers.CharField(required=False, allow_blank=True, default="")
    template_version_code = serializers.CharField(required=False, allow_blank=True, default="")
    template_version_id = serializers.UUIDField(required=False, allow_null=True)

    runtime_payload = serializers.JSONField(required=False, default=dict)
    database_values = serializers.JSONField(required=False, default=dict)
    connector_values = serializers.JSONField(required=False, default=dict)
    computed_values = serializers.JSONField(required=False, default=dict)
    render_options = serializers.JSONField(required=False, default=dict)
    layout_options = serializers.JSONField(required=False, default=dict)
    style_overrides = serializers.CharField(required=False, allow_blank=True, default="")
    business_reference = serializers.CharField(required=False, allow_blank=True, default="")
    correlation_id = serializers.CharField(required=False, allow_blank=True, default="")

    program_code = serializers.CharField(required=False, allow_blank=True, default="")
    module_name = serializers.CharField(required=False, allow_blank=True, default="")
    application_name = serializers.CharField(required=False, allow_blank=True, default="")

    @staticmethod
    def _validated_json(value, field_name: str):
        try:
            return validate_json(value)
        except DjangoValidationError as exc:
            raise serializers.ValidationError(str(exc)) from exc

    def validate_variable_group_code(self, value: str) -> str:
        return value.strip()

    def validate_rule_group_code(self, value: str) -> str:
        return value.strip()

    def validate_connector_code(self, value: str) -> str:
        return value.strip()

    def validate_template_code(self, value: str) -> str:
        return value.strip()

    def validate_template_version_code(self, value: str) -> str:
        return value.strip()

    def validate_program_code(self, value: str) -> str:
        return value.strip()

    def validate_module_name(self, value: str) -> str:
        return value.strip()

    def validate_application_name(self, value: str) -> str:
        return value.strip()

    def validate_business_reference(self, value: str) -> str:
        return value.strip()

    def validate_correlation_id(self, value: str) -> str:
        return value.strip()

    def validate(self, attrs):
        attrs = super().validate(attrs)
        generation_request_id = attrs.get("generation_request_id")
        document_id = attrs.get("document_id")
        template_code = (attrs.get("template_code") or "").strip()
        template_version_code = (attrs.get("template_version_code") or "").strip()
        template_version_id = attrs.get("template_version_id")
        business_reference = (attrs.get("business_reference") or "").strip()
        correlation_id = (attrs.get("correlation_id") or "").strip()

        if not generation_request_id and not any(
            [document_id, template_code, template_version_code, template_version_id]
        ):
            raise serializers.ValidationError(
                "Provide generation_request_id or at least one of document_id/template details."
            )

        if business_reference and correlation_id and business_reference != correlation_id:
            raise serializers.ValidationError(
                {"correlation_id": "correlation_id must match business_reference when both are provided."}
            )

        if correlation_id and not business_reference:
            attrs["business_reference"] = correlation_id

        return attrs

    def validate_runtime_payload(self, value):
        validated = self._validated_json(value, "runtime_payload")
        if not isinstance(validated, dict):
            raise serializers.ValidationError("runtime_payload must be a JSON object.")
        return validated

    def validate_database_values(self, value):
        validated = self._validated_json(value, "database_values")
        if not isinstance(validated, dict):
            raise serializers.ValidationError("database_values must be a JSON object.")
        return validated

    def validate_connector_values(self, value):
        validated = self._validated_json(value, "connector_values")
        if not isinstance(validated, dict):
            raise serializers.ValidationError("connector_values must be a JSON object.")
        return validated

    def validate_computed_values(self, value):
        validated = self._validated_json(value, "computed_values")
        if not isinstance(validated, dict):
            raise serializers.ValidationError("computed_values must be a JSON object.")
        return validated

    def validate_render_options(self, value):
        validated = self._validated_json(value, "render_options")
        if not isinstance(validated, dict):
            raise serializers.ValidationError("render_options must be a JSON object.")
        return validated

    def validate_layout_options(self, value):
        validated = self._validated_json(value, "layout_options")
        if not isinstance(validated, dict):
            raise serializers.ValidationError("layout_options must be a JSON object.")
        return validated

    def validate_connector_payload(self, value):
        validated = self._validated_json(value, "connector_payload")
        if not isinstance(validated, dict):
            raise serializers.ValidationError("connector_payload must be a JSON object.")
        return validated


class RuntimeGenerateRequestSerializer(RuntimePreviewRequestSerializer):
    generation_request_id = serializers.UUIDField(required=True)
    output_format = serializers.ChoiceField(
        choices=[OutputFormatChoices.PDF, OutputFormatChoices.DOCX],
        required=False,
        default=OutputFormatChoices.PDF,
    )
    file_name = serializers.CharField(required=False, allow_blank=True, default="")
