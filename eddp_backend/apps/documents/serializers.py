from __future__ import annotations

from typing import Any

from rest_framework import serializers

from apps.common.serializers import BaseAuditModelSerializer

from .models import Document, DocumentCategory, DocumentDefinition, DocumentPackage


class DocumentCategorySerializer(BaseAuditModelSerializer):
    class Meta:
        model = DocumentCategory
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


class DocumentNestedSerializer(serializers.ModelSerializer):
    class Meta:
        model = Document
        fields = ("id", "code", "name", "document_type", "output_format")


class DocumentSerializer(BaseAuditModelSerializer):
    category = DocumentCategorySerializer(read_only=True)
    category_id = serializers.UUIDField(write_only=True, required=False)
    product = serializers.ListField(
        child=serializers.CharField(max_length=100),
        allow_empty=False,
    )

    class Meta:
        model = Document
        fields = (
            "id",
            "code",
            "category",
            "category_id",
            "name",
            "document_type",
            "business_module",
            "product",
            "output_format",
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

    VALID_BUSINESS_MODULES = {"PRIME", "EB"}
    VALID_PRODUCTS = {"HOME LOAN", "PLOT LOAN", "LAP"}

    def validate_name(self, value: str) -> str:
        return self.ensure_non_empty(value, "name")

    def validate_business_module(self, value: str) -> str:
        normalized = self.ensure_non_empty(value, "business_module").upper()
        if normalized not in self.VALID_BUSINESS_MODULES:
            raise serializers.ValidationError("business_module must be one of PRIME or EB.")
        return normalized

    def validate_product(self, value: list[str]) -> list[str]:
        if not value:
            raise serializers.ValidationError("At least one product is required.")

        normalized_values: list[str] = []
        seen: set[str] = set()
        for product_value in value:
            normalized = self.ensure_non_empty(product_value, "product").upper()
            if normalized not in self.VALID_PRODUCTS:
                raise serializers.ValidationError(
                    "product values must be selected from HOME LOAN, PLOT LOAN, or LAP."
                )
            if normalized not in seen:
                seen.add(normalized)
                normalized_values.append(normalized)

        return normalized_values

    @staticmethod
    def _product_to_list(value: Any) -> list[str]:
        if value is None:
            return []
        if isinstance(value, list):
            return value
        if isinstance(value, str):
            parsed = [item.strip() for item in value.split(",") if item.strip()]
            return parsed
        return []

    def to_internal_value(self, data):
        mutable = dict(data)
        if "product" in mutable:
            mutable["product"] = self._product_to_list(mutable.get("product"))
        return super().to_internal_value(mutable)

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation["product"] = self._product_to_list(getattr(instance, "product", None))
        representation["category_id"] = str(getattr(instance, "category_id", ""))
        return representation

    def validate(self, attrs):
        attrs = super().validate(attrs)
        category = attrs.get("category") or getattr(self.instance, "category", None)
        category_id = attrs.get("category_id") or getattr(self.instance, "category_id", None)
        if category is None and category_id is not None:
            category = DocumentCategory.all_objects.filter(id=category_id).first()
        name = attrs.get("name") or getattr(self.instance, "name", None)

        if category and name:
            queryset = Document.all_objects.filter(category=category, name=name)
            if self.instance is not None:
                queryset = queryset.exclude(pk=self.instance.pk)
            if queryset.exists():
                raise serializers.ValidationError(
                    {"name": "Document name must be unique within the selected category."}
                )

        return attrs


class DocumentDefinitionSerializer(BaseAuditModelSerializer):
    document = DocumentNestedSerializer(read_only=True)
    document_id = serializers.PrimaryKeyRelatedField(
        source="document",
        queryset=Document.objects.all(),
        write_only=True,
    )

    class Meta:
        model = DocumentDefinition
        fields = (
            "id",
            "code",
            "document",
            "document_id",
            "active_template_code",
            "variable_group_code",
            "connector_code",
            "rule_group_code",
            "language",
            "effective_from",
            "effective_to",
            "status",
            "created_at",
            "updated_at",
            "created_by",
            "updated_by",
            "is_deleted",
            "deleted_at",
        )
        read_only_fields = BaseAuditModelSerializer.AUDIT_READONLY_FIELDS

    def validate(self, attrs):
        attrs = super().validate(attrs)
        effective_from = attrs.get("effective_from") or getattr(self.instance, "effective_from", None)
        effective_to = attrs.get("effective_to")
        if effective_to is None and self.instance is not None:
            effective_to = self.instance.effective_to

        if effective_from and effective_to and effective_to <= effective_from:
            raise serializers.ValidationError(
                {"effective_to": "effective_to must be greater than effective_from."}
            )
        return attrs


class DocumentPackageSerializer(BaseAuditModelSerializer):
    documents = DocumentNestedSerializer(many=True, read_only=True)
    document_ids = serializers.PrimaryKeyRelatedField(
        source="documents",
        queryset=Document.objects.all(),
        many=True,
        write_only=True,
        required=False,
    )

    class Meta:
        model = DocumentPackage
        fields = (
            "id",
            "code",
            "name",
            "description",
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

    def validate_name(self, value: str) -> str:
        return self.ensure_non_empty(value, "name")

    def validate_document_ids(self, value):
        ids = [str(item.id) for item in value]
        if len(ids) != len(set(ids)):
            raise serializers.ValidationError("document_ids must not contain duplicates.")
        return value
