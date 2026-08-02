from __future__ import annotations

from typing import Any

from django.db import transaction
from django.db.models import Q, QuerySet

from .models import Variable


class VariableRepository:
    model = Variable

    def get_all(self, query_params: dict[str, Any] | None = None) -> QuerySet[Variable]:
        queryset = self.model.objects.select_related("group", "group__category").prefetch_related("documents").all()
        params = query_params or {}

        status = (params.get("status") or "").strip()
        if status:
            queryset = queryset.filter(status__iexact=status)

        group_id = (params.get("group_id") or "").strip()
        if group_id:
            queryset = queryset.filter(group_id=group_id)

        # Filter by document_id (for template designer)
        document_id = (params.get("document_id") or "").strip()
        if document_id:
            queryset = queryset.filter(documents__id=document_id).distinct()

        search = (params.get("search") or "").strip()
        if search:
            queryset = queryset.filter(
                Q(code__icontains=search)
                | Q(name__icontains=search)
                | Q(display_name__icontains=search)
                | Q(description__icontains=search)
                | Q(data_type__icontains=search)
                | Q(source_type__icontains=search)
                | Q(source_reference__icontains=search)
                | Q(group__code__icontains=search)
                | Q(group__name__icontains=search)
                | Q(group__category__name__icontains=search)
            )

        return queryset

    def get_by_id(self, id: Any) -> Variable | None:
        return self.model.objects.select_related("group").prefetch_related("documents").filter(id=id).first()

    def get_by_code(self, code: str) -> Variable | None:
        return self.model.objects.select_related("group").prefetch_related("documents").filter(code=code).first()

    @transaction.atomic
    def create(self, data: dict[str, Any]) -> Variable:
        # Extract document_ids before creating instance
        document_ids = data.pop("_document_ids", None)
        instance = self.model.objects.create(**data)
        # Handle many-to-many relationship
        if document_ids is not None:
            instance.documents.set(document_ids)
        return instance

    @transaction.atomic
    def update(self, instance: Variable, data: dict[str, Any]) -> Variable:
        # Extract document_ids before updating instance
        document_ids = data.pop("_document_ids", None)
        for field, value in data.items():
            setattr(instance, field, value)
        if data:
            instance.save(update_fields=list(data.keys()))
        else:
            instance.save()
        # Handle many-to-many relationship
        if document_ids is not None:
            instance.documents.set(document_ids)
        instance.refresh_from_db()
        return instance

    @transaction.atomic
    def soft_delete(self, instance: Variable) -> Variable:
        instance.soft_delete()
        return instance

    @transaction.atomic
    def restore(self, instance: Variable) -> Variable:
        instance.restore()
        return instance

    def exists(self, code: str) -> bool:
        return self.model.objects.filter(code=code).exists()