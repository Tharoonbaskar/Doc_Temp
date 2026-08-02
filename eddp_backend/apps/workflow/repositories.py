from __future__ import annotations

from typing import Any

from django.db import transaction
from django.db.models import Q, QuerySet

from .models import Workflow


class WorkflowRepository:
    model = Workflow

    def get_all(self, query_params: dict[str, Any] | None = None) -> QuerySet[Workflow]:
        queryset = self.model.objects.select_related("applicable_document").all()
        params = query_params or {}

        status = (params.get("status") or "").strip()
        if status:
            queryset = queryset.filter(status__iexact=status)

        document_id = (params.get("document_id") or "").strip()
        if document_id:
            queryset = queryset.filter(applicable_document_id=document_id)

        workflow_type = (params.get("workflow_type") or "").strip()
        if workflow_type:
            queryset = queryset.filter(workflow_type__iexact=workflow_type)

        is_default = (params.get("is_default") or "").strip().lower()
        if is_default in {"true", "false"}:
            queryset = queryset.filter(is_default=(is_default == "true"))

        search = (params.get("search") or "").strip()
        if search:
            queryset = queryset.filter(
                Q(code__icontains=search)
                | Q(name__icontains=search)
                | Q(description__icontains=search)
                | Q(workflow_type__icontains=search)
                | Q(applicable_document__code__icontains=search)
                | Q(applicable_document__name__icontains=search)
            )

        return queryset

    def get_by_id(self, id: Any) -> Workflow | None:
        return self.model.objects.filter(id=id).first()

    def get_by_code(self, code: str) -> Workflow | None:
        return self.model.objects.filter(code=code).first()

    @transaction.atomic
    def create(self, data: dict[str, Any]) -> Workflow:
        return self.model.objects.create(**data)

    @transaction.atomic
    def update(self, instance: Workflow, data: dict[str, Any]) -> Workflow:
        for field, value in data.items():
            setattr(instance, field, value)
        if data:
            instance.save(update_fields=list(data.keys()))
        else:
            instance.save()
        return instance

    @transaction.atomic
    def soft_delete(self, instance: Workflow) -> Workflow:
        instance.soft_delete()
        return instance

    @transaction.atomic
    def restore(self, instance: Workflow) -> Workflow:
        instance.restore()
        return instance

    def exists(self, code: str) -> bool:
        return self.model.objects.filter(code=code).exists()