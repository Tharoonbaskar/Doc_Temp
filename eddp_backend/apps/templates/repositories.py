from __future__ import annotations

from typing import Any

from django.db import transaction
from django.db.models import Q, QuerySet

from .models import Template, TemplateVersion


class TemplateRepository:
    model = Template

    def get_all(self, query_params: dict[str, Any] | None = None) -> QuerySet[Template]:
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
                | Q(name__icontains=search)
                | Q(description__icontains=search)
                | Q(category__icontains=search)
                | Q(template_type__icontains=search)
                | Q(content_type__icontains=search)
                | Q(document__code__icontains=search)
                | Q(document__name__icontains=search)
            )

        return queryset

    def get_by_id(self, id: Any) -> Template | None:
        return self.model.objects.select_related("document").filter(id=id).first()

    def get_by_code(self, code: str) -> Template | None:
        return self.model.objects.select_related("document").filter(code=code).first()

    def get_deleted_by_code(self, code: str) -> Template | None:
        return self.model.all_objects.select_related("document").filter(code=code, is_deleted=True).first()

    def get_deleted_by_document_and_name(self, document: Any, name: str) -> Template | None:
        return (
            self.model.all_objects.select_related("document")
            .filter(document=document, name=name, is_deleted=True)
            .first()
        )

    @transaction.atomic
    def create(self, data: dict[str, Any]) -> Template:
        return self.model.objects.create(**data)

    @transaction.atomic
    def update(self, instance: Template, data: dict[str, Any]) -> Template:
        for field, value in data.items():
            setattr(instance, field, value)
        if data:
            instance.save(update_fields=list(data.keys()))
        else:
            instance.save()
        return instance

    @transaction.atomic
    def soft_delete(self, instance: Template) -> Template:
        instance.soft_delete()
        return instance

    @transaction.atomic
    def restore(self, instance: Template) -> Template:
        instance.restore()
        return instance

    def exists(self, code: str) -> bool:
        return self.model.objects.filter(code=code).exists()


class TemplateVersionRepository:
    model = TemplateVersion

    def get_all(self, query_params: dict[str, Any] | None = None) -> QuerySet[TemplateVersion]:
        queryset = self.model.objects.select_related("template", "template__document").all()
        params = query_params or {}

        status = (params.get("status") or "").strip()
        if status:
            queryset = queryset.filter(status__iexact=status)

        template_id = (params.get("template_id") or "").strip()
        if template_id:
            queryset = queryset.filter(template_id=template_id)

        search = (params.get("search") or "").strip()
        if search:
            queryset = queryset.filter(
                Q(code__icontains=search)
                | Q(version_name__icontains=search)
                | Q(change_summary__icontains=search)
                | Q(template__code__icontains=search)
                | Q(template__name__icontains=search)
            )

        return queryset

    def get_by_id(self, id: Any) -> TemplateVersion | None:
        return self.model.objects.select_related("template", "template__document").filter(id=id).first()

    def get_by_code(self, code: str) -> TemplateVersion | None:
        return self.model.objects.select_related("template", "template__document").filter(code=code).first()

    @transaction.atomic
    def create(self, data: dict[str, Any]) -> TemplateVersion:
        return self.model.objects.create(**data)

    @transaction.atomic
    def update(self, instance: TemplateVersion, data: dict[str, Any]) -> TemplateVersion:
        for field, value in data.items():
            setattr(instance, field, value)
        if data:
            instance.save(update_fields=list(data.keys()))
        else:
            instance.save()
        return instance

    @transaction.atomic
    def soft_delete(self, instance: TemplateVersion) -> TemplateVersion:
        instance.soft_delete()
        return instance

    @transaction.atomic
    def restore(self, instance: TemplateVersion) -> TemplateVersion:
        instance.restore()
        return instance

    def exists(self, code: str) -> bool:
        return self.model.objects.filter(code=code).exists()