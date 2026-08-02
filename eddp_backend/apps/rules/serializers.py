from __future__ import annotations

from rest_framework import serializers

from apps.common.serializers import BaseAuditModelSerializer

from .models import Rule, RuleGroup


class RuleGroupSerializer(BaseAuditModelSerializer):
    class Meta:
        model = RuleGroup
        fields = (
            "id",
            "code",
            "name",
            "description",
            "priority",
            "status",
            "created_at",
            "updated_at",
            "created_by",
            "updated_by",
            "is_deleted",
            "deleted_at",
        )
        read_only_fields = BaseAuditModelSerializer.AUDIT_READONLY_FIELDS

    def validate_name(self, value: str) -> str:
        return self.ensure_non_empty(value, "name")

    def validate_priority(self, value: int) -> int:
        if value < 0:
            raise serializers.ValidationError("priority cannot be negative.")
        return value


class RuleGroupNestedSerializer(serializers.ModelSerializer):
    class Meta:
        model = RuleGroup
        fields = ("id", "code", "name", "priority")


class RuleSerializer(BaseAuditModelSerializer):
    rule_group = RuleGroupNestedSerializer(read_only=True)
    rule_group_id = serializers.UUIDField(write_only=True, required=False)

    class Meta:
        model = Rule
        fields = (
            "id",
            "code",
            "rule_group",
            "rule_group_id",
            "name",
            "description",
            "expression",
            "rule_type",
            "execution_order",
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

    def validate_name(self, value: str) -> str:
        return self.ensure_non_empty(value, "name")

    def validate_expression(self, value: str) -> str:
        return self.ensure_non_empty(value, "expression")

    def validate_execution_order(self, value: int) -> int:
        if value < 1:
            raise serializers.ValidationError("execution_order must be greater than zero.")
        return value

    def validate(self, attrs):
        attrs = super().validate(attrs)
        rule_group = attrs.get("rule_group") or getattr(self.instance, "rule_group", None)
        rule_group_id = attrs.get("rule_group_id") or getattr(self.instance, "rule_group_id", None)
        if rule_group is None and rule_group_id is not None:
            rule_group = RuleGroup.all_objects.filter(id=rule_group_id).first()
        name = attrs.get("name") or getattr(self.instance, "name", None)

        if rule_group and name:
            queryset = Rule.all_objects.filter(rule_group=rule_group, name=name)
            if self.instance is not None:
                queryset = queryset.exclude(pk=self.instance.pk)
            if queryset.exists():
                raise serializers.ValidationError(
                    {"name": "Rule name must be unique within the selected group."}
                )

        return attrs

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation["rule_group_id"] = str(getattr(instance, "rule_group_id", ""))
        return representation
