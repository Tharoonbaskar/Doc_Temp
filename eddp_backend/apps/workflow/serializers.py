from __future__ import annotations

from django.contrib.auth import get_user_model
from rest_framework import serializers

from apps.common.serializers import BaseAuditModelSerializer, UserSummarySerializer
from apps.documents.models import Document
from apps.identity.models import Role

from .models import Workflow, WorkflowHistory, WorkflowStep


class DocumentReferenceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Document
        fields = ("id", "code", "name")


class RoleReferenceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Role
        fields = ("id", "code", "name")


class WorkflowNestedSerializer(serializers.ModelSerializer):
    class Meta:
        model = Workflow
        fields = ("id", "code", "name", "workflow_type", "version")


class WorkflowStepNestedSerializer(serializers.ModelSerializer):
    class Meta:
        model = WorkflowStep
        fields = ("id", "code", "step_name", "step_order", "action_type")


class WorkflowSerializer(BaseAuditModelSerializer):
    applicable_document = DocumentReferenceSerializer(read_only=True)
    applicable_document_id = serializers.PrimaryKeyRelatedField(
        source="applicable_document",
        queryset=Document.objects.all(),
        write_only=True,
    )

    class Meta:
        model = Workflow
        fields = (
            "id",
            "code",
            "name",
            "description",
            "workflow_type",
            "applicable_document",
            "applicable_document_id",
            "version",
            "is_default",
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

    def validate_workflow_type(self, value: str) -> str:
        return self.ensure_non_empty(value, "workflow_type")

    def validate_version(self, value: int) -> int:
        if value < 1:
            raise serializers.ValidationError("version must be greater than zero.")
        return value


class WorkflowStepSerializer(BaseAuditModelSerializer):
    workflow = WorkflowNestedSerializer(read_only=True)
    workflow_id = serializers.PrimaryKeyRelatedField(
        source="workflow",
        queryset=Workflow.objects.all(),
        write_only=True,
    )
    approver_role = RoleReferenceSerializer(read_only=True)
    approver_role_id = serializers.PrimaryKeyRelatedField(
        source="approver_role",
        queryset=Role.objects.all(),
        write_only=True,
    )

    class Meta:
        model = WorkflowStep
        fields = (
            "id",
            "code",
            "workflow",
            "workflow_id",
            "step_name",
            "step_order",
            "approver_role",
            "approver_role_id",
            "action_type",
            "is_mandatory",
            "status",
            "created_at",
            "updated_at",
            "created_by",
            "updated_by",
            "is_deleted",
            "deleted_at",
        )
        read_only_fields = BaseAuditModelSerializer.AUDIT_READONLY_FIELDS

    def validate_step_name(self, value: str) -> str:
        return self.ensure_non_empty(value, "step_name")

    def validate_step_order(self, value: int) -> int:
        if value < 1:
            raise serializers.ValidationError("step_order must be greater than zero.")
        return value

    def validate(self, attrs):
        attrs = super().validate(attrs)
        workflow = attrs.get("workflow") or getattr(self.instance, "workflow", None)
        step_order = attrs.get("step_order") or getattr(self.instance, "step_order", None)

        if workflow and step_order is not None:
            queryset = WorkflowStep.all_objects.filter(workflow=workflow, step_order=step_order)
            if self.instance is not None:
                queryset = queryset.exclude(pk=self.instance.pk)
            if queryset.exists():
                raise serializers.ValidationError(
                    {"step_order": "step_order must be unique within the selected workflow."}
                )

        return attrs


class WorkflowHistorySerializer(BaseAuditModelSerializer):
    workflow = WorkflowNestedSerializer(read_only=True)
    workflow_id = serializers.PrimaryKeyRelatedField(
        source="workflow",
        queryset=Workflow.objects.all(),
        write_only=True,
    )
    current_step = WorkflowStepNestedSerializer(read_only=True)
    current_step_id = serializers.PrimaryKeyRelatedField(
        source="current_step",
        queryset=WorkflowStep.objects.all(),
        write_only=True,
        required=False,
        allow_null=True,
    )
    performed_by = UserSummarySerializer(read_only=True)
    performed_by_id = serializers.PrimaryKeyRelatedField(
        source="performed_by",
        queryset=get_user_model().objects.all(),
        write_only=True,
        required=False,
        allow_null=True,
    )

    class Meta:
        model = WorkflowHistory
        fields = (
            "id",
            "code",
            "workflow",
            "workflow_id",
            "document_reference",
            "current_step",
            "current_step_id",
            "performed_by",
            "performed_by_id",
            "action",
            "remarks",
            "performed_at",
            "status",
            "created_at",
            "updated_at",
            "created_by",
            "updated_by",
            "is_deleted",
            "deleted_at",
        )
        read_only_fields = BaseAuditModelSerializer.AUDIT_READONLY_FIELDS + ("performed_at",)

    def validate_document_reference(self, value: str) -> str:
        return self.ensure_non_empty(value, "document_reference")
