from __future__ import annotations

from typing import Iterable
from typing import Any

from django.forms.models import model_to_dict
from django.utils import timezone
from rest_framework import status
from rest_framework.response import Response

from apps.common.exceptions import (
    BaseApplicationException,
    DuplicateResourceException,
    ResourceNotFoundException,
    ValidationException,
)
from apps.common.responses import error_response, success_response
from apps.runtime.models import GeneratedDocument, GenerationRequest

from .repositories import (
    ActivityLogRepository,
    GovernanceIntegrationRepository,
    GovernanceRepository,
    SnapshotRepository,
)


class GovernanceService:
    """Service layer for Governance aggregate operations."""

    def __init__(self, repository: GovernanceRepository | None = None) -> None:
        self.repository = repository or GovernanceRepository()

    @staticmethod
    def _serialize(instance: Any) -> dict[str, Any]:
        data = model_to_dict(instance)
        data["id"] = str(instance.id)
        data["code"] = instance.code
        data["status"] = instance.status
        data["is_deleted"] = instance.is_deleted
        data["created_at"] = instance.created_at.isoformat() if instance.created_at else None
        data["updated_at"] = instance.updated_at.isoformat() if instance.updated_at else None
        data["deleted_at"] = instance.deleted_at.isoformat() if instance.deleted_at else None
        return data

    @staticmethod
    def _error(exc: BaseApplicationException) -> Response:
        detail = exc.detail
        message = detail if isinstance(detail, str) else "Request failed."
        errors = exc.errors if getattr(exc, "errors", None) else detail
        return error_response(
            message=message,
            errors=errors,
            status_code=exc.status_code,
            error_code=getattr(exc, "default_code", "application_error"),
        )

    @staticmethod
    def _validate_payload(data: dict[str, Any]) -> None:
        if not isinstance(data, dict):
            raise ValidationException(detail="Payload must be a JSON object.")

    def _get_instance_or_raise(self, id: Any):
        if not id:
            raise ValidationException(detail="Field 'id' is required.")
        instance = self.repository.get_by_id(id)
        if not instance:
            raise ResourceNotFoundException(detail="Resource not found.")
        return instance

    def get_all(self, query_params: dict[str, Any] | None = None) -> Response:
        try:
            records = [self._serialize(item) for item in self.repository.get_all(query_params=query_params)]
            return success_response(data=records, message="Records fetched successfully.")
        except BaseApplicationException as exc:
            return self._error(exc)

    def get_by_id(self, id: Any) -> Response:
        try:
            instance = self._get_instance_or_raise(id)
            return success_response(data=self._serialize(instance), message="Record fetched successfully.")
        except BaseApplicationException as exc:
            return self._error(exc)

    def get_by_code(self, code: str) -> Response:
        try:
            if not code:
                raise ValidationException(detail="Field 'code' is required.")
            instance = self.repository.get_by_code(code)
            if not instance:
                raise ResourceNotFoundException(detail="Resource not found.")
            return success_response(data=self._serialize(instance), message="Record fetched successfully.")
        except BaseApplicationException as exc:
            return self._error(exc)

    def create(self, data: dict[str, Any]) -> Response:
        try:
            self._validate_payload(data)
            code = data.get("code")
            if not code:
                raise ValidationException(detail="Field 'code' is required.")
            if self.repository.exists(code):
                raise DuplicateResourceException(detail=f"Resource with code '{code}' already exists.")
            instance = self.repository.create(data)
            return success_response(
                data=self._serialize(instance),
                message="Record created successfully.",
                status_code=status.HTTP_201_CREATED,
            )
        except BaseApplicationException as exc:
            return self._error(exc)

    def update(self, id: Any, data: dict[str, Any]) -> Response:
        try:
            self._validate_payload(data)
            instance = self._get_instance_or_raise(id)
            new_code = data.get("code")
            if new_code:
                existing = self.repository.get_by_code(new_code)
                if existing and existing.id != instance.id:
                    raise DuplicateResourceException(detail=f"Resource with code '{new_code}' already exists.")
            updated = self.repository.update(instance, data)
            return success_response(data=self._serialize(updated), message="Record updated successfully.")
        except BaseApplicationException as exc:
            return self._error(exc)

    def soft_delete(self, id: Any) -> Response:
        try:
            instance = self._get_instance_or_raise(id)
            deleted = self.repository.soft_delete(instance)
            return success_response(data=self._serialize(deleted), message="Record deleted successfully.")
        except BaseApplicationException as exc:
            return self._error(exc)

    def delete(self, id: Any) -> Response:
        return self.soft_delete(id)

    def restore(self, id: Any) -> Response:
        try:
            instance = self._get_instance_or_raise(id)
            restored = self.repository.restore(instance)
            return success_response(data=self._serialize(restored), message="Record restored successfully.")
        except BaseApplicationException as exc:
            return self._error(exc)

    def exists(self, code: str) -> Response:
        try:
            if not code:
                raise ValidationException(detail="Field 'code' is required.")
            return success_response(data={"exists": self.repository.exists(code)}, message="Lookup completed.")
        except BaseApplicationException as exc:
            return self._error(exc)


class ActivityLogService:
    """Service layer for ActivityLog aggregate operations."""

    def __init__(self, repository: ActivityLogRepository | None = None) -> None:
        self.repository = repository or ActivityLogRepository()

    @staticmethod
    def _serialize(instance: Any) -> dict[str, Any]:
        data = model_to_dict(instance)
        data["id"] = str(instance.id)
        data["code"] = instance.code
        performed_by = getattr(instance, "performed_by", None)
        data["performed_by"] = (
            {
                "id": str(performed_by.id),
                "username": performed_by.username,
                "email": getattr(performed_by, "email", ""),
                "first_name": getattr(performed_by, "first_name", ""),
                "last_name": getattr(performed_by, "last_name", ""),
            }
            if performed_by is not None
            else None
        )
        data["status"] = instance.status
        data["is_deleted"] = instance.is_deleted
        data["created_at"] = instance.created_at.isoformat() if instance.created_at else None
        data["updated_at"] = instance.updated_at.isoformat() if instance.updated_at else None
        data["deleted_at"] = instance.deleted_at.isoformat() if instance.deleted_at else None
        data["activity_time"] = instance.activity_time.isoformat() if instance.activity_time else None
        return data

    @staticmethod
    def _error(exc: BaseApplicationException) -> Response:
        detail = exc.detail
        message = detail if isinstance(detail, str) else "Request failed."
        errors = exc.errors if getattr(exc, "errors", None) else detail
        return error_response(
            message=message,
            errors=errors,
            status_code=exc.status_code,
            error_code=getattr(exc, "default_code", "application_error"),
        )

    @staticmethod
    def _validate_payload(data: dict[str, Any]) -> None:
        if not isinstance(data, dict):
            raise ValidationException(detail="Payload must be a JSON object.")

    def _get_instance_or_raise(self, id: Any):
        if not id:
            raise ValidationException(detail="Field 'id' is required.")
        instance = self.repository.get_by_id(id)
        if not instance:
            raise ResourceNotFoundException(detail="Resource not found.")
        return instance

    def get_all(self, query_params: dict[str, Any] | None = None) -> Response:
        try:
            records = [self._serialize(item) for item in self.repository.get_all(query_params=query_params)]
            return success_response(data=records, message="Records fetched successfully.")
        except BaseApplicationException as exc:
            return self._error(exc)

    def get_by_id(self, id: Any) -> Response:
        try:
            instance = self._get_instance_or_raise(id)
            return success_response(data=self._serialize(instance), message="Record fetched successfully.")
        except BaseApplicationException as exc:
            return self._error(exc)

    def get_by_code(self, code: str) -> Response:
        try:
            if not code:
                raise ValidationException(detail="Field 'code' is required.")
            instance = self.repository.get_by_code(code)
            if not instance:
                raise ResourceNotFoundException(detail="Resource not found.")
            return success_response(data=self._serialize(instance), message="Record fetched successfully.")
        except BaseApplicationException as exc:
            return self._error(exc)

    def create(self, data: dict[str, Any]) -> Response:
        try:
            self._validate_payload(data)
            code = data.get("code")
            if not code:
                raise ValidationException(detail="Field 'code' is required.")
            if self.repository.exists(code):
                raise DuplicateResourceException(detail=f"Resource with code '{code}' already exists.")
            instance = self.repository.create(data)
            return success_response(
                data=self._serialize(instance),
                message="Record created successfully.",
                status_code=status.HTTP_201_CREATED,
            )
        except BaseApplicationException as exc:
            return self._error(exc)

    def update(self, id: Any, data: dict[str, Any]) -> Response:
        try:
            self._validate_payload(data)
            instance = self._get_instance_or_raise(id)
            new_code = data.get("code")
            if new_code:
                existing = self.repository.get_by_code(new_code)
                if existing and existing.id != instance.id:
                    raise DuplicateResourceException(detail=f"Resource with code '{new_code}' already exists.")
            updated = self.repository.update(instance, data)
            return success_response(data=self._serialize(updated), message="Record updated successfully.")
        except BaseApplicationException as exc:
            return self._error(exc)

    def soft_delete(self, id: Any) -> Response:
        try:
            instance = self._get_instance_or_raise(id)
            deleted = self.repository.soft_delete(instance)
            return success_response(data=self._serialize(deleted), message="Record deleted successfully.")
        except BaseApplicationException as exc:
            return self._error(exc)

    def delete(self, id: Any) -> Response:
        return self.soft_delete(id)

    def restore(self, id: Any) -> Response:
        try:
            instance = self._get_instance_or_raise(id)
            restored = self.repository.restore(instance)
            return success_response(data=self._serialize(restored), message="Record restored successfully.")
        except BaseApplicationException as exc:
            return self._error(exc)

    def exists(self, code: str) -> Response:
        try:
            if not code:
                raise ValidationException(detail="Field 'code' is required.")
            return success_response(data={"exists": self.repository.exists(code)}, message="Lookup completed.")
        except BaseApplicationException as exc:
            return self._error(exc)


class SnapshotService:
    """Service layer for Snapshot aggregate operations."""

    def __init__(self, repository: SnapshotRepository | None = None) -> None:
        self.repository = repository or SnapshotRepository()

    @staticmethod
    def _serialize(instance: Any) -> dict[str, Any]:
        data = model_to_dict(instance)
        data["id"] = str(instance.id)
        data["code"] = instance.code
        generated_document = getattr(instance, "generated_document", None)
        data["generated_document"] = (
            {
                "id": str(generated_document.id),
                "code": generated_document.code,
                "file_name": generated_document.file_name,
                "checksum": generated_document.checksum,
            }
            if generated_document is not None
            else None
        )
        data["status"] = instance.status
        data["is_deleted"] = instance.is_deleted
        data["created_at"] = instance.created_at.isoformat() if instance.created_at else None
        data["updated_at"] = instance.updated_at.isoformat() if instance.updated_at else None
        data["deleted_at"] = instance.deleted_at.isoformat() if instance.deleted_at else None
        data["created_on"] = instance.created_on.isoformat() if instance.created_on else None
        return data

    @staticmethod
    def _error(exc: BaseApplicationException) -> Response:
        detail = exc.detail
        message = detail if isinstance(detail, str) else "Request failed."
        errors = exc.errors if getattr(exc, "errors", None) else detail
        return error_response(
            message=message,
            errors=errors,
            status_code=exc.status_code,
            error_code=getattr(exc, "default_code", "application_error"),
        )

    @staticmethod
    def _validate_payload(data: dict[str, Any]) -> None:
        if not isinstance(data, dict):
            raise ValidationException(detail="Payload must be a JSON object.")

    def _get_instance_or_raise(self, id: Any):
        if not id:
            raise ValidationException(detail="Field 'id' is required.")
        instance = self.repository.get_by_id(id)
        if not instance:
            raise ResourceNotFoundException(detail="Resource not found.")
        return instance

    def get_all(self, query_params: dict[str, Any] | None = None) -> Response:
        try:
            records = [self._serialize(item) for item in self.repository.get_all(query_params=query_params)]
            return success_response(data=records, message="Records fetched successfully.")
        except BaseApplicationException as exc:
            return self._error(exc)

    def get_by_id(self, id: Any) -> Response:
        try:
            instance = self._get_instance_or_raise(id)
            return success_response(data=self._serialize(instance), message="Record fetched successfully.")
        except BaseApplicationException as exc:
            return self._error(exc)

    def get_by_code(self, code: str) -> Response:
        try:
            if not code:
                raise ValidationException(detail="Field 'code' is required.")
            instance = self.repository.get_by_code(code)
            if not instance:
                raise ResourceNotFoundException(detail="Resource not found.")
            return success_response(data=self._serialize(instance), message="Record fetched successfully.")
        except BaseApplicationException as exc:
            return self._error(exc)

    def create(self, data: dict[str, Any]) -> Response:
        try:
            self._validate_payload(data)
            code = data.get("code")
            if not code:
                raise ValidationException(detail="Field 'code' is required.")
            if self.repository.exists(code):
                raise DuplicateResourceException(detail=f"Resource with code '{code}' already exists.")
            instance = self.repository.create(data)
            return success_response(
                data=self._serialize(instance),
                message="Record created successfully.",
                status_code=status.HTTP_201_CREATED,
            )
        except BaseApplicationException as exc:
            return self._error(exc)

    def update(self, id: Any, data: dict[str, Any]) -> Response:
        try:
            self._validate_payload(data)
            instance = self._get_instance_or_raise(id)
            new_code = data.get("code")
            if new_code:
                existing = self.repository.get_by_code(new_code)
                if existing and existing.id != instance.id:
                    raise DuplicateResourceException(detail=f"Resource with code '{new_code}' already exists.")
            updated = self.repository.update(instance, data)
            return success_response(data=self._serialize(updated), message="Record updated successfully.")
        except BaseApplicationException as exc:
            return self._error(exc)

    def soft_delete(self, id: Any) -> Response:
        try:
            instance = self._get_instance_or_raise(id)
            deleted = self.repository.soft_delete(instance)
            return success_response(data=self._serialize(deleted), message="Record deleted successfully.")
        except BaseApplicationException as exc:
            return self._error(exc)

    def delete(self, id: Any) -> Response:
        return self.soft_delete(id)

    def restore(self, id: Any) -> Response:
        try:
            instance = self._get_instance_or_raise(id)
            restored = self.repository.restore(instance)
            return success_response(data=self._serialize(restored), message="Record restored successfully.")
        except BaseApplicationException as exc:
            return self._error(exc)

    def exists(self, code: str) -> Response:
        try:
            if not code:
                raise ValidationException(detail="Field 'code' is required.")
            return success_response(data={"exists": self.repository.exists(code)}, message="Lookup completed.")
        except BaseApplicationException as exc:
            return self._error(exc)


class GovernanceIntegrationService:
    def __init__(self, repository: GovernanceIntegrationRepository | None = None) -> None:
        self.repository = repository or GovernanceIntegrationRepository()

    @staticmethod
    def _client_ip(request) -> str:
        x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR", "") if request else ""
        if x_forwarded_for:
            return x_forwarded_for.split(",")[0].strip()
        return request.META.get("REMOTE_ADDR", "") if request else ""

    @staticmethod
    def _user_agent(request) -> str:
        return (request.META.get("HTTP_USER_AGENT", "")[:512] if request else "")

    def record_generation(
        self,
        *,
        generation_request: GenerationRequest,
        generated_document: GeneratedDocument,
        output_format: str,
        variable_count: int,
        rule_count: int,
        connector_count: int,
        execution_history: Iterable[dict[str, Any]],
        request=None,
        performed_by=None,
    ) -> dict[str, Any]:
        snapshot_payload = {
            "generated_document_id": str(generated_document.id),
            "generation_request_id": str(generation_request.id),
            "request_id": str(generation_request.request_id),
            "business_reference": generation_request.business_reference,
            "file_name": generated_document.file_name,
            "file_path": generated_document.file_path,
            "file_type": generated_document.file_type,
            "checksum": generated_document.checksum,
            "generated_at": generated_document.generated_at.isoformat() if generated_document.generated_at else None,
            "recorded_at": timezone.now().isoformat(),
        }

        snapshot = self.repository.upsert_snapshot(
            generated_document=generated_document,
            snapshot_json=snapshot_payload,
            performed_by=performed_by,
        )

        audit_log = self.repository.create_audit_log(
            entity_name="GeneratedDocument",
            entity_id=str(generated_document.id),
            action="GENERATE_DOCUMENT",
            old_value={},
            new_value=snapshot_payload,
            performed_by=performed_by,
            ip_address=self._client_ip(request),
            user_agent=self._user_agent(request),
        )

        activity_log = self.repository.create_activity_log(
            module="RUNTIME",
            activity="DOCUMENT_GENERATED",
            reference_number=generation_request.business_reference or str(generation_request.request_id),
            description=(
                f"Document generated for request_id={generation_request.request_id} "
                f"output={output_format} file={generated_document.file_name}"
            ),
            performed_by=performed_by,
        )

        metric_payload = {
            "request_id": str(generation_request.request_id),
            "generated_document_id": str(generated_document.id),
            "output_format": output_format,
            "generated_at": generated_document.generated_at.isoformat() if generated_document.generated_at else None,
        }
        metric = self.repository.upsert_generation_metric(
            generation_request=generation_request,
            generated_document=generated_document,
            output_format=output_format,
            processing_time_ms=int(generation_request.processing_time_ms or 0),
            variable_count=variable_count,
            rule_count=rule_count,
            connector_count=connector_count,
            metric_json=metric_payload,
            performed_by=performed_by,
        )

        self.repository.reset_execution_history(generation_request)
        history_records = []
        for index, entry in enumerate(execution_history, start=1):
            history_records.append(
                self.repository.create_execution_history(
                    generation_request=generation_request,
                    stage_name=str(entry.get("stage") or f"STEP_{index}"),
                    stage_status=str(entry.get("status") or "SUCCESS"),
                    sequence_no=index,
                    started_at=entry.get("started_at"),
                    completed_at=entry.get("completed_at"),
                    duration_ms=int(entry.get("duration_ms") or 0),
                    details_json=entry.get("details") or {},
                    performed_by=performed_by,
                )
            )

        return {
            "snapshot_id": str(snapshot.id),
            "audit_log_id": str(audit_log.id),
            "activity_log_id": str(activity_log.id),
            "generation_metric_id": str(metric.id),
            "execution_history_count": len(history_records),
        }

    def record_preview(
        self,
        *,
        generation_request: GenerationRequest,
        execution_history: Iterable[dict[str, Any]],
        request=None,
        performed_by=None,
    ) -> dict[str, Any]:
        audit_log = self.repository.create_audit_log(
            entity_name="GenerationRequest",
            entity_id=str(generation_request.id),
            action="PREVIEW_DOCUMENT",
            old_value={},
            new_value={
                "request_id": str(generation_request.request_id),
                "business_reference": generation_request.business_reference,
                "previewed_at": timezone.now().isoformat(),
            },
            performed_by=performed_by,
            ip_address=self._client_ip(request),
            user_agent=self._user_agent(request),
        )

        activity_log = self.repository.create_activity_log(
            module="RUNTIME",
            activity="DOCUMENT_PREVIEWED",
            reference_number=generation_request.business_reference or str(generation_request.request_id),
            description=f"Preview generated for request_id={generation_request.request_id}",
            performed_by=performed_by,
        )

        self.repository.reset_execution_history(generation_request)
        history_count = 0
        for index, entry in enumerate(execution_history, start=1):
            self.repository.create_execution_history(
                generation_request=generation_request,
                stage_name=str(entry.get("stage") or f"STEP_{index}"),
                stage_status=str(entry.get("status") or "SUCCESS"),
                sequence_no=index,
                started_at=entry.get("started_at"),
                completed_at=entry.get("completed_at"),
                duration_ms=int(entry.get("duration_ms") or 0),
                details_json=entry.get("details") or {},
                performed_by=performed_by,
            )
            history_count += 1

        return {
            "audit_log_id": str(audit_log.id),
            "activity_log_id": str(activity_log.id),
            "execution_history_count": history_count,
        }

    def record_download(
        self,
        *,
        generation_request: GenerationRequest,
        generated_document: GeneratedDocument,
        request=None,
        performed_by=None,
    ) -> dict[str, Any]:
        audit_log = self.repository.create_audit_log(
            entity_name="GeneratedDocument",
            entity_id=str(generated_document.id),
            action="DOWNLOAD_DOCUMENT",
            old_value={},
            new_value={
                "request_id": str(generation_request.request_id),
                "file_name": generated_document.file_name,
                "file_path": generated_document.file_path,
                "downloaded_at": timezone.now().isoformat(),
            },
            performed_by=performed_by,
            ip_address=self._client_ip(request),
            user_agent=self._user_agent(request),
        )

        activity_log = self.repository.create_activity_log(
            module="RUNTIME",
            activity="DOCUMENT_DOWNLOADED",
            reference_number=generation_request.business_reference or str(generation_request.request_id),
            description=f"Download requested for request_id={generation_request.request_id}",
            performed_by=performed_by,
        )

        return {
            "audit_log_id": str(audit_log.id),
            "activity_log_id": str(activity_log.id),
        }
