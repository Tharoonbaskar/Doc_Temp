from __future__ import annotations

from typing import Any

from rest_framework import serializers


class UserSummarySerializer(serializers.Serializer):
    id = serializers.IntegerField(read_only=True)
    username = serializers.CharField(read_only=True)
    email = serializers.EmailField(read_only=True, allow_blank=True)
    first_name = serializers.CharField(read_only=True, allow_blank=True)
    last_name = serializers.CharField(read_only=True, allow_blank=True)


class BaseAuditModelSerializer(serializers.ModelSerializer):
    """Base serializer with common audit-field handling and validations."""

    AUDIT_READONLY_FIELDS = (
        "id",
        "created_at",
        "updated_at",
        "created_by",
        "updated_by",
        "is_deleted",
        "deleted_at",
    )

    def validate_code(self, value: str) -> str:
        normalized = (value or "").strip().upper()
        if not normalized:
            raise serializers.ValidationError("Code is required.")
        return normalized

    @staticmethod
    def ensure_non_empty(value: str, field_name: str) -> str:
        normalized = (value or "").strip()
        if not normalized:
            raise serializers.ValidationError(f"{field_name} may not be blank.")
        return normalized

    @staticmethod
    def ensure_json_compatible(value: Any, field_name: str) -> Any:
        if value is None:
            return value
        if not isinstance(value, (dict, list)):
            raise serializers.ValidationError(
                f"{field_name} must be a JSON object or array."
            )
        return value
