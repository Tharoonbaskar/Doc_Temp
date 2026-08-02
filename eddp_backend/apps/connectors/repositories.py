from __future__ import annotations

from typing import Any

from django.db import transaction
from django.db.models import Q, QuerySet

from .models import Connector


class ConnectorRepository:
    model = Connector

    def get_all(self, query_params: dict[str, Any] | None = None) -> QuerySet[Connector]:
        queryset = self.model.objects.all()
        params = query_params or {}

        status = (params.get("status") or "").strip()
        if status:
            queryset = queryset.filter(status__iexact=status)

        connector_type = (params.get("connector_type") or "").strip()
        if connector_type:
            queryset = queryset.filter(connector_type__iexact=connector_type)

        is_active = (params.get("is_active") or "").strip().lower()
        if is_active in {"true", "false"}:
            queryset = queryset.filter(is_active=(is_active == "true"))

        search = (params.get("search") or "").strip()
        if search:
            queryset = queryset.filter(
                Q(code__icontains=search)
                | Q(name__icontains=search)
                | Q(description__icontains=search)
                | Q(connector_type__icontains=search)
                | Q(host__icontains=search)
                | Q(database_name__icontains=search)
                | Q(username__icontains=search)
                | Q(api_base_url__icontains=search)
            )

        return queryset

    def get_by_id(self, id: Any) -> Connector | None:
        return self.model.objects.filter(id=id).first()

    def get_by_code(self, code: str) -> Connector | None:
        return self.model.objects.filter(code=code).first()

    @transaction.atomic
    def create(self, data: dict[str, Any]) -> Connector:
        return self.model.objects.create(**data)

    @transaction.atomic
    def update(self, instance: Connector, data: dict[str, Any]) -> Connector:
        for field, value in data.items():
            setattr(instance, field, value)
        if data:
            instance.save(update_fields=list(data.keys()))
        else:
            instance.save()
        return instance

    @transaction.atomic
    def soft_delete(self, instance: Connector) -> Connector:
        instance.soft_delete()
        return instance

    @transaction.atomic
    def restore(self, instance: Connector) -> Connector:
        instance.restore()
        return instance

    def exists(self, code: str) -> bool:
        return self.model.objects.filter(code=code).exists()