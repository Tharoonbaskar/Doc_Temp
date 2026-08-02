from __future__ import annotations

from typing import Any

from django.db import transaction
from django.db.models import Q, QuerySet

from .models import Document, DocumentDefinition


class DocumentRepository:
    model = Document

    def get_all(self, query_params: dict[str, Any] | None = None) -> QuerySet[Document]:
        queryset = self.model.objects.select_related("category").all()
        params = query_params or {}

        status = (params.get("status") or "").strip()
        if status:
            queryset = queryset.filter(status__iexact=status)

        category_id = (params.get("category_id") or "").strip()
        if category_id:
            queryset = queryset.filter(category_id=category_id)

        search = (params.get("search") or "").strip()
        if search:
            queryset = queryset.filter(
                Q(code__icontains=search)
                | Q(name__icontains=search)
                | Q(document_type__icontains=search)
                | Q(business_module__icontains=search)
                | Q(product__icontains=search)
                | Q(output_format__icontains=search)
                | Q(description__icontains=search)
                | Q(category__code__icontains=search)
                | Q(category__name__icontains=search)
            )

        return queryset

    def get_by_id(self, id: Any) -> Document | None:
        return self.model.objects.select_related("category").filter(id=id).first()

    def get_by_code(self, code: str) -> Document | None:
        return self.model.objects.select_related("category").filter(code=code).first()

    @transaction.atomic
    def create(self, data: dict[str, Any]) -> Document:
        return self.model.objects.create(**data)

    @transaction.atomic
    def update(self, instance: Document, data: dict[str, Any]) -> Document:
        for field, value in data.items():
            setattr(instance, field, value)
        if data:
            instance.save(update_fields=list(data.keys()))
        else:
            instance.save()
        return instance

    @transaction.atomic
    def soft_delete(self, instance: Document) -> Document:
        instance.soft_delete()
        return instance

    @transaction.atomic
    def restore(self, instance: Document) -> Document:
        instance.restore()
        return instance

    def exists(self, code: str) -> bool:
        return self.model.objects.filter(code=code).exists()


class DocumentDefinitionRepository:
    model = DocumentDefinition

    def get_all(self, query_params: dict[str, Any] | None = None) -> QuerySet[DocumentDefinition]:
        queryset = self.model.objects.select_related("document").all()
        params = query_params or {}

        status = (params.get("status") or "").strip()
        if status:
            queryset = queryset.filter(status__iexact=status)

        document_id = (params.get("document_id") or "").strip()
        if document_id:
            queryset = queryset.filter(document_id=document_id)

        search = (params.get("search") or "").strip()
        if search:
            queryset = queryset.filter(
                Q(code__icontains=search)
                | Q(active_template_code__icontains=search)
                | Q(variable_group_code__icontains=search)
                | Q(connector_code__icontains=search)
                | Q(rule_group_code__icontains=search)
                | Q(language__icontains=search)
                | Q(document__code__icontains=search)
                | Q(document__name__icontains=search)
            )

        return queryset

    def get_by_id(self, id: Any) -> DocumentDefinition | None:
        return self.model.objects.select_related("document").filter(id=id).first()

    def get_by_code(self, code: str) -> DocumentDefinition | None:
        return self.model.objects.select_related("document").filter(code=code).first()

    @transaction.atomic
    def create(self, data: dict[str, Any]) -> DocumentDefinition:
        return self.model.objects.create(**data)

    @transaction.atomic
    def update(self, instance: DocumentDefinition, data: dict[str, Any]) -> DocumentDefinition:
        for field, value in data.items():
            setattr(instance, field, value)
        if data:
            instance.save(update_fields=list(data.keys()))
        else:
            instance.save()
        return instance

    @transaction.atomic
    def soft_delete(self, instance: DocumentDefinition) -> DocumentDefinition:
        instance.soft_delete()
        return instance

    @transaction.atomic
    def restore(self, instance: DocumentDefinition) -> DocumentDefinition:
        instance.restore()
        return instance

    def exists(self, code: str) -> bool:
        return self.model.objects.filter(code=code).exists()