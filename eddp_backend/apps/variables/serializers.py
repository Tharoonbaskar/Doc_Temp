from __future__ import annotations

from rest_framework import serializers

from apps.common.serializers import BaseAuditModelSerializer

from .models import Variable, VariableCategory, VariableGroup


class VariableCategorySerializer(BaseAuditModelSerializer):
    class Meta:
        model = VariableCategory
        fields = (
            "id",
            "code",
            "name",
            "description",
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


class VariableGroupNestedSerializer(serializers.ModelSerializer):
    class Meta:
        model = VariableGroup
        fields = ("id", "code", "name")


class VariableGroupSerializer(BaseAuditModelSerializer):
    category = VariableCategorySerializer(read_only=True)
    category_id = serializers.PrimaryKeyRelatedField(
        source="category",
        queryset=VariableCategory.objects.all(),
        write_only=True,
    )

    class Meta:
        model = VariableGroup
        fields = (
            "id",
            "code",
            "name",
            "description",
            "category",
            "category_id",
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

    def validate(self, attrs):
        attrs = super().validate(attrs)
        category = attrs.get("category") or getattr(self.instance, "category", None)
        name = attrs.get("name") or getattr(self.instance, "name", None)

        if category and name:
            queryset = VariableGroup.all_objects.filter(category=category, name=name)
            if self.instance is not None:
                queryset = queryset.exclude(pk=self.instance.pk)
            if queryset.exists():
                raise serializers.ValidationError(
                    {"name": "Group name must be unique within the selected category."}
                )

        return attrs


class VariableSerializer(BaseAuditModelSerializer):
    group = VariableGroupNestedSerializer(read_only=True)
    group_id = serializers.UUIDField(write_only=True, required=False)
    document_ids = serializers.ListField(
        child=serializers.UUIDField(),
        write_only=True,
        required=False,
        allow_empty=True,
    )
    documents = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Variable
        fields = (
            "id",
            "code",
            "group",
            "group_id",
            "name",
            "display_name",
            "description",
            "data_type",
            "source_type",
            "source_reference",
            "default_value",
            "is_required",
            "documents",
            "document_ids",
            "status",
            "created_at",
            "updated_at",
            "created_by",
            "updated_by",
            "is_deleted",
            "deleted_at",
        )
        read_only_fields = BaseAuditModelSerializer.AUDIT_READONLY_FIELDS

    def get_documents(self, obj):
        """Return list of associated documents with minimal info"""
        return [
            {
                "id": str(doc.id),
                "name": doc.name,
                "document_type": doc.document_type,
            }
            for doc in obj.documents.all()
        ]

    def create(self, validated_data):
        document_ids = validated_data.pop("document_ids", [])
        variable = super().create(validated_data)
        if document_ids:
            variable.documents.set(document_ids)
        return variable

    def update(self, instance, validated_data):
        document_ids = validated_data.pop("document_ids", None)
        variable = super().update(instance, validated_data)
        if document_ids is not None:
            variable.documents.set(document_ids)
        return variable

    def validate_name(self, value: str) -> str:
        return self.ensure_non_empty(value, "name")

    def validate_display_name(self, value: str) -> str:
        return self.ensure_non_empty(value, "display_name")

    def validate(self, attrs):
        attrs = super().validate(attrs)
        group = attrs.get("group") or getattr(self.instance, "group", None)
        group_id = attrs.get("group_id") or getattr(self.instance, "group_id", None)
        if group is None and group_id is not None:
            group = VariableGroup.all_objects.filter(id=group_id).first()
        name = attrs.get("name") or getattr(self.instance, "name", None)

        if group and name:
            queryset = Variable.all_objects.filter(group=group, name=name)
            if self.instance is not None:
                queryset = queryset.exclude(pk=self.instance.pk)
            if queryset.exists():
                raise serializers.ValidationError(
                    {"name": "Variable name must be unique within the selected group."}
                )

        return attrs

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation["group_id"] = str(getattr(instance, "group_id", ""))
        return representation
