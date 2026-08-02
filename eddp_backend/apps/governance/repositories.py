from __future__ import annotations

import uuid
from typing import Any

from django.db import transaction
from django.db.models import Q, QuerySet

from apps.common.choices import OutputFormatChoices, StatusChoices
from apps.runtime.models import GeneratedDocument, GenerationRequest

from .models import ActivityLog, AuditLog, ExecutionHistory, GenerationMetric, Snapshot


class GovernanceRepository:
    model = AuditLog

    def get_all(self, query_params: dict[str, Any] | None = None) -> QuerySet[AuditLog]:
        queryset = self.model.objects.select_related("performed_by").all()
        params = query_params or {}

        status = (params.get("status") or "").strip()
        if status:
            queryset = queryset.filter(status__iexact=status)

        entity_name = (params.get("entity_name") or "").strip()
        if entity_name:
            queryset = queryset.filter(entity_name__icontains=entity_name)

        action = (params.get("action") or "").strip()
        if action:
            queryset = queryset.filter(action__icontains=action)

        search = (params.get("search") or "").strip()
        if search:
            queryset = queryset.filter(
                Q(code__icontains=search)
                | Q(entity_name__icontains=search)
                | Q(entity_id__icontains=search)
                | Q(action__icontains=search)
                | Q(performed_by__username__icontains=search)
                | Q(user_agent__icontains=search)
            )

        return queryset

    def get_by_id(self, id: Any) -> AuditLog | None:
        return self.model.objects.filter(id=id).first()

    def get_by_code(self, code: str) -> AuditLog | None:
        return self.model.objects.filter(code=code).first()

    @transaction.atomic
    def create(self, data: dict[str, Any]) -> AuditLog:
        return self.model.objects.create(**data)

    @transaction.atomic
    def update(self, instance: AuditLog, data: dict[str, Any]) -> AuditLog:
        for field, value in data.items():
            setattr(instance, field, value)
        if data:
            instance.save(update_fields=list(data.keys()))
        else:
            instance.save()
        return instance

    @transaction.atomic
    def soft_delete(self, instance: AuditLog) -> AuditLog:
        instance.soft_delete()
        return instance

    @transaction.atomic
    def restore(self, instance: AuditLog) -> AuditLog:
        instance.restore()
        return instance

    def exists(self, code: str) -> bool:
        return self.model.objects.filter(code=code).exists()


class ActivityLogRepository:
    model = ActivityLog

    def get_all(self, query_params: dict[str, Any] | None = None) -> QuerySet[ActivityLog]:
        queryset = self.model.objects.select_related("performed_by").all()
        params = query_params or {}

        status = (params.get("status") or "").strip()
        if status:
            queryset = queryset.filter(status__iexact=status)

        module = (params.get("module") or "").strip()
        if module:
            queryset = queryset.filter(module__iexact=module)

        activity = (params.get("activity") or "").strip()
        if activity:
            queryset = queryset.filter(activity__icontains=activity)

        reference_number = (params.get("reference_number") or "").strip()
        if reference_number:
            queryset = queryset.filter(reference_number__icontains=reference_number)

        search = (params.get("search") or "").strip()
        if search:
            queryset = queryset.filter(
                Q(code__icontains=search)
                | Q(module__icontains=search)
                | Q(activity__icontains=search)
                | Q(reference_number__icontains=search)
                | Q(description__icontains=search)
                | Q(performed_by__username__icontains=search)
            )

        return queryset

    def get_by_id(self, id: Any) -> ActivityLog | None:
        return self.model.objects.select_related("performed_by").filter(id=id).first()

    def get_by_code(self, code: str) -> ActivityLog | None:
        return self.model.objects.select_related("performed_by").filter(code=code).first()

    @transaction.atomic
    def create(self, data: dict[str, Any]) -> ActivityLog:
        return self.model.objects.create(**data)

    @transaction.atomic
    def update(self, instance: ActivityLog, data: dict[str, Any]) -> ActivityLog:
        for field, value in data.items():
            setattr(instance, field, value)
        if data:
            instance.save(update_fields=list(data.keys()))
        else:
            instance.save()
        return instance

    @transaction.atomic
    def soft_delete(self, instance: ActivityLog) -> ActivityLog:
        instance.soft_delete()
        return instance

    @transaction.atomic
    def restore(self, instance: ActivityLog) -> ActivityLog:
        instance.restore()
        return instance

    def exists(self, code: str) -> bool:
        return self.model.objects.filter(code=code).exists()


class SnapshotRepository:
    model = Snapshot

    def get_all(self, query_params: dict[str, Any] | None = None) -> QuerySet[Snapshot]:
        queryset = self.model.objects.select_related("generated_document").all()
        params = query_params or {}

        status = (params.get("status") or "").strip()
        if status:
            queryset = queryset.filter(status__iexact=status)

        generated_document_id = (params.get("generated_document_id") or "").strip()
        if generated_document_id:
            queryset = queryset.filter(generated_document_id=generated_document_id)

        search = (params.get("search") or "").strip()
        if search:
            queryset = queryset.filter(
                Q(code__icontains=search)
                | Q(generated_document__code__icontains=search)
                | Q(generated_document__file_name__icontains=search)
                | Q(generated_document__checksum__icontains=search)
            )

        return queryset

    def get_by_id(self, id: Any) -> Snapshot | None:
        return self.model.objects.select_related("generated_document").filter(id=id).first()

    def get_by_code(self, code: str) -> Snapshot | None:
        return self.model.objects.select_related("generated_document").filter(code=code).first()

    @transaction.atomic
    def create(self, data: dict[str, Any]) -> Snapshot:
        return self.model.objects.create(**data)

    @transaction.atomic
    def update(self, instance: Snapshot, data: dict[str, Any]) -> Snapshot:
        for field, value in data.items():
            setattr(instance, field, value)
        if data:
            instance.save(update_fields=list(data.keys()))
        else:
            instance.save()
        return instance

    @transaction.atomic
    def soft_delete(self, instance: Snapshot) -> Snapshot:
        instance.soft_delete()
        return instance

    @transaction.atomic
    def restore(self, instance: Snapshot) -> Snapshot:
        instance.restore()
        return instance

    def exists(self, code: str) -> bool:
        return self.model.objects.filter(code=code).exists()


class GovernanceIntegrationRepository:
    @staticmethod
    def _code(prefix: str) -> str:
        return f"{prefix}-{uuid.uuid4().hex[:12].upper()}"

    @transaction.atomic
    def upsert_snapshot(
        self,
        *,
        generated_document: GeneratedDocument,
        snapshot_json: dict[str, Any],
        performed_by=None,
    ) -> Snapshot:
        snapshot = Snapshot.objects.filter(generated_document=generated_document).first()
        if snapshot is None:
            return Snapshot.objects.create(
                code=self._code("SNP"),
                generated_document=generated_document,
                snapshot_version=1,
                snapshot_json=snapshot_json,
                status=StatusChoices.ACTIVE,
                created_by=performed_by if getattr(performed_by, "is_authenticated", False) else None,
                updated_by=performed_by if getattr(performed_by, "is_authenticated", False) else None,
            )

        snapshot.snapshot_version = int(snapshot.snapshot_version or 0) + 1
        snapshot.snapshot_json = snapshot_json
        snapshot.status = StatusChoices.ACTIVE
        if getattr(performed_by, "is_authenticated", False):
            snapshot.updated_by = performed_by
        snapshot.save(update_fields=["snapshot_version", "snapshot_json", "status", "updated_by"])
        return snapshot

    @transaction.atomic
    def create_audit_log(
        self,
        *,
        entity_name: str,
        entity_id: str,
        action: str,
        old_value: dict[str, Any] | None,
        new_value: dict[str, Any] | None,
        performed_by=None,
        ip_address: str = "",
        user_agent: str = "",
    ) -> AuditLog:
        return AuditLog.objects.create(
            code=self._code("AUD"),
            entity_name=entity_name,
            entity_id=entity_id,
            action=action,
            old_value=old_value or {},
            new_value=new_value or {},
            performed_by=performed_by if getattr(performed_by, "is_authenticated", False) else None,
            ip_address=ip_address or None,
            user_agent=(user_agent or "")[:512],
            status=StatusChoices.ACTIVE,
        )

    @transaction.atomic
    def create_activity_log(
        self,
        *,
        module: str,
        activity: str,
        reference_number: str,
        description: str,
        performed_by=None,
    ) -> ActivityLog:
        return ActivityLog.objects.create(
            code=self._code("ACT"),
            module=module,
            activity=activity,
            reference_number=reference_number,
            description=description,
            performed_by=performed_by if getattr(performed_by, "is_authenticated", False) else None,
            status=StatusChoices.ACTIVE,
        )

    @transaction.atomic
    def upsert_generation_metric(
        self,
        *,
        generation_request: GenerationRequest,
        generated_document: GeneratedDocument | None,
        output_format: str,
        processing_time_ms: int,
        variable_count: int,
        rule_count: int,
        connector_count: int,
        metric_json: dict[str, Any],
        performed_by=None,
    ) -> GenerationMetric:
        normalized_format = output_format if output_format in OutputFormatChoices.values else OutputFormatChoices.PDF
        metric = GenerationMetric.objects.filter(generation_request=generation_request).first()

        if metric is None:
            return GenerationMetric.objects.create(
                code=self._code("MET"),
                generation_request=generation_request,
                generated_document=generated_document,
                business_reference=generation_request.business_reference,
                request_source=generation_request.request_source,
                output_format=normalized_format,
                processing_time_ms=max(0, int(processing_time_ms or 0)),
                variable_count=max(0, int(variable_count or 0)),
                rule_count=max(0, int(rule_count or 0)),
                connector_count=max(0, int(connector_count or 0)),
                metric_json=metric_json or {},
                status=StatusChoices.ACTIVE,
                created_by=performed_by if getattr(performed_by, "is_authenticated", False) else None,
                updated_by=performed_by if getattr(performed_by, "is_authenticated", False) else None,
            )

        metric.generated_document = generated_document
        metric.business_reference = generation_request.business_reference
        metric.request_source = generation_request.request_source
        metric.output_format = normalized_format
        metric.processing_time_ms = max(0, int(processing_time_ms or 0))
        metric.variable_count = max(0, int(variable_count or 0))
        metric.rule_count = max(0, int(rule_count or 0))
        metric.connector_count = max(0, int(connector_count or 0))
        metric.metric_json = metric_json or {}
        metric.status = StatusChoices.ACTIVE
        if getattr(performed_by, "is_authenticated", False):
            metric.updated_by = performed_by
        metric.save(
            update_fields=[
                "generated_document",
                "business_reference",
                "request_source",
                "output_format",
                "processing_time_ms",
                "variable_count",
                "rule_count",
                "connector_count",
                "metric_json",
                "status",
                "updated_by",
            ]
        )
        return metric

    @transaction.atomic
    def reset_execution_history(self, generation_request: GenerationRequest) -> None:
        ExecutionHistory.objects.filter(generation_request=generation_request).delete()

    @transaction.atomic
    def create_execution_history(
        self,
        *,
        generation_request: GenerationRequest,
        stage_name: str,
        stage_status: str,
        sequence_no: int,
        started_at,
        completed_at,
        duration_ms: int,
        details_json: dict[str, Any] | None,
        performed_by=None,
    ) -> ExecutionHistory:
        return ExecutionHistory.objects.create(
            code=self._code("EXH"),
            generation_request=generation_request,
            stage_name=stage_name,
            stage_status=stage_status,
            sequence_no=max(1, int(sequence_no or 1)),
            started_at=started_at,
            completed_at=completed_at,
            duration_ms=max(0, int(duration_ms or 0)),
            details_json=details_json or {},
            status=StatusChoices.ACTIVE,
            created_by=performed_by if getattr(performed_by, "is_authenticated", False) else None,
            updated_by=performed_by if getattr(performed_by, "is_authenticated", False) else None,
        )

    def get_execution_history(self, generation_request: GenerationRequest) -> QuerySet[ExecutionHistory]:
        return ExecutionHistory.objects.filter(generation_request=generation_request).order_by("sequence_no")

    def get_generation_metric(self, generation_request: GenerationRequest) -> GenerationMetric | None:
        return GenerationMetric.objects.filter(generation_request=generation_request).first()