from __future__ import annotations

from rest_framework import serializers

from apps.common.serializers import BaseAuditModelSerializer

from .models import Connector, ConnectorConfiguration


class ConnectorNestedSerializer(serializers.ModelSerializer):
    class Meta:
        model = Connector
        fields = ("id", "code", "name", "connector_type", "is_active")


class ConnectorSerializer(BaseAuditModelSerializer):
    class Meta:
        model = Connector
        fields = (
            "id",
            "code",
            "name",
            "connector_type",
            "description",
            "host",
            "port",
            "database_name",
            "username",
            "password",
            "api_base_url",
            "timeout",
            "retry_count",
            "is_active",
            "status",
            "created_at",
            "updated_at",
            "created_by",
            "updated_by",
            "is_deleted",
            "deleted_at",
        )
        read_only_fields = BaseAuditModelSerializer.AUDIT_READONLY_FIELDS
        extra_kwargs = {
            "password": {"write_only": True, "required": False},
        }

    def validate_name(self, value: str) -> str:
        return self.ensure_non_empty(value, "name")

    def validate_timeout(self, value: int) -> int:
        if value < 1:
            raise serializers.ValidationError("timeout must be greater than zero.")
        return value

    def validate_retry_count(self, value: int) -> int:
        if value < 0:
            raise serializers.ValidationError("retry_count cannot be negative.")
        return value


class ConnectorConfigurationSerializer(BaseAuditModelSerializer):
    connector = ConnectorNestedSerializer(read_only=True)
    connector_id = serializers.PrimaryKeyRelatedField(
        source="connector",
        queryset=Connector.objects.all(),
        write_only=True,
    )

    class Meta:
        model = ConnectorConfiguration
        fields = (
            "id",
            "code",
            "connector",
            "connector_id",
            "configuration_json",
            "headers_json",
            "authentication_type",
            "authentication_json",
            "status",
            "created_at",
            "updated_at",
            "created_by",
            "updated_by",
            "is_deleted",
            "deleted_at",
        )
        read_only_fields = BaseAuditModelSerializer.AUDIT_READONLY_FIELDS

    def validate_configuration_json(self, value):
        return self.ensure_json_compatible(value, "configuration_json")

    def validate_headers_json(self, value):
        validated = self.ensure_json_compatible(value, "headers_json")
        if validated is not None and not isinstance(validated, dict):
            raise serializers.ValidationError("headers_json must be a JSON object.")
        return validated

    def validate_authentication_json(self, value):
        validated = self.ensure_json_compatible(value, "authentication_json")
        if validated is not None and not isinstance(validated, dict):
            raise serializers.ValidationError("authentication_json must be a JSON object.")
        return validated
