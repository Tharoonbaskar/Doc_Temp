from __future__ import annotations

from typing import Any

from django.db import transaction
from django.db.models import Q, QuerySet

from .models import Rule


class RuleRepository:
    model = Rule

    def get_all(self, query_params: dict[str, Any] | None = None) -> QuerySet[Rule]:
        queryset = self.model.objects.select_related("rule_group").all()
        params = query_params or {}

        status = (params.get("status") or "").strip()
        if status:
            queryset = queryset.filter(status__iexact=status)

        rule_group_id = (params.get("rule_group_id") or "").strip()
        if rule_group_id:
            queryset = queryset.filter(rule_group_id=rule_group_id)

        rule_type = (params.get("rule_type") or "").strip()
        if rule_type:
            queryset = queryset.filter(rule_type__iexact=rule_type)

        is_active = (params.get("is_active") or "").strip().lower()
        if is_active in {"true", "false"}:
            queryset = queryset.filter(is_active=(is_active == "true"))

        search = (params.get("search") or "").strip()
        if search:
            queryset = queryset.filter(
                Q(code__icontains=search)
                | Q(name__icontains=search)
                | Q(description__icontains=search)
                | Q(expression__icontains=search)
                | Q(rule_type__icontains=search)
                | Q(rule_group__code__icontains=search)
                | Q(rule_group__name__icontains=search)
            )

        return queryset

    def get_by_id(self, id: Any) -> Rule | None:
        return self.model.objects.select_related("rule_group").filter(id=id).first()

    def get_by_code(self, code: str) -> Rule | None:
        return self.model.objects.select_related("rule_group").filter(code=code).first()

    @transaction.atomic
    def create(self, data: dict[str, Any]) -> Rule:
        return self.model.objects.create(**data)

    @transaction.atomic
    def update(self, instance: Rule, data: dict[str, Any]) -> Rule:
        for field, value in data.items():
            setattr(instance, field, value)
        if data:
            instance.save(update_fields=list(data.keys()))
        else:
            instance.save()
        return instance

    @transaction.atomic
    def soft_delete(self, instance: Rule) -> Rule:
        instance.soft_delete()
        return instance

    @transaction.atomic
    def restore(self, instance: Rule) -> Rule:
        instance.restore()
        return instance

    def exists(self, code: str) -> bool:
        return self.model.objects.filter(code=code).exists()