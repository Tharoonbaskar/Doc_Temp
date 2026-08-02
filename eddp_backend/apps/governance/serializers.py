from __future__ import annotations

from django.contrib.auth import get_user_model
from rest_framework import serializers

from apps.common.serializers import BaseAuditModelSerializer, UserSummarySerializer
from apps.runtime.models import GeneratedDocument

from .models import ActivityLog, AuditLog, Snapshot


class GeneratedDocumentReferenceSerializer(serializers.ModelSerializer):
    class Meta:
        model = GeneratedDocument
        fields = ("id", "code", "file_name", "checksum")


class SnapshotSerializer(BaseAuditModelSerializer):
    generated_document = GeneratedDocumentReferenceSerializer(read_only=True)
    generated_document_id = serializers.PrimaryKeyRelatedField(
        source="generated_document",
        queryset=GeneratedDocument.objects.all(),
        write_only=True,
    )

    class Meta:
        model = Snapshot
        fields = (
            "id",
            "code",
            "generated_document",
            "generated_document_id",
            "snapshot_version",
            "snapshot_json",
            "created_on",
            "status",
            "created_at",
            "updated_at",
            "created_by",
            "updated_by",
            "is_deleted",
            "deleted_at",
        )
        read_only_fields = BaseAuditModelSerializer.AUDIT_READONLY_FIELDS + ("created_on",)

    def validate_snapshot_version(self, value: int) -> int:
        if value < 1:
            raise serializers.ValidationError("snapshot_version must be greater than zero.")
        return value

    def validate_snapshot_json(self, value):
        validated = self.ensure_json_compatible(value, "snapshot_json")
        if validated is not None and not isinstance(validated, dict):
            raise serializers.ValidationError("snapshot_json must be a JSON object.")
        return validated


class AuditLogSerializer(BaseAuditModelSerializer):
    performed_by = UserSummarySerializer(read_only=True)
    performed_by_id = serializers.PrimaryKeyRelatedField(
        source="performed_by",
        queryset=get_user_model().objects.all(),
        write_only=True,
        required=False,
        allow_null=True,
    )

    class Meta:
        model = AuditLog
        fields = (
            "id",
            "code",
            "entity_name",
            "entity_id",
            "action",
            "old_value",
            "new_value",
            "performed_by",
            "performed_by_id",
            "ip_address",
            "user_agent",
            "created_on",
            "status",
            "created_at",
            "updated_at",
            "created_by",
            "updated_by",
            "is_deleted",
            "deleted_at",
        )
        read_only_fields = BaseAuditModelSerializer.AUDIT_READONLY_FIELDS + ("created_on",)

    def validate_entity_name(self, value: str) -> str:
        return self.ensure_non_empty(value, "entity_name")

    def validate_entity_id(self, value: str) -> str:
        return self.ensure_non_empty(value, "entity_id")

    def validate_action(self, value: str) -> str:
        return self.ensure_non_empty(value, "action")

    def validate_old_value(self, value):
        validated = self.ensure_json_compatible(value, "old_value")
        if validated is not None and not isinstance(validated, dict):
            raise serializers.ValidationError("old_value must be a JSON object.")
        return validated

    def validate_new_value(self, value):
        validated = self.ensure_json_compatible(value, "new_value")
        if validated is not None and not isinstance(validated, dict):
            raise serializers.ValidationError("new_value must be a JSON object.")
        return validated


class ActivityLogSerializer(BaseAuditModelSerializer):
    performed_by = UserSummarySerializer(read_only=True)
    performed_by_id = serializers.PrimaryKeyRelatedField(
        source="performed_by",
        queryset=get_user_model().objects.all(),
        write_only=True,
        required=False,
        allow_null=True,
    )

    class Meta:
        model = ActivityLog
        fields = (
            "id",
            "code",
            "module",
            "activity",
            "reference_number",
            "description",
            "performed_by",
            "performed_by_id",
            "activity_time",
            "status",
            "created_at",
            "updated_at",
            "created_by",
            "updated_by",
            "is_deleted",
            "deleted_at",
        )
        read_only_fields = BaseAuditModelSerializer.AUDIT_READONLY_FIELDS + ("activity_time",)

    def validate_module(self, value: str) -> str:
        return self.ensure_non_empty(value, "module")

    def validate_activity(self, value: str) -> str:
        return self.ensure_non_empty(value, "activity")
