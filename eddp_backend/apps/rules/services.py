from __future__ import annotations

from typing import Any
import uuid

from django.forms.models import model_to_dict
from rest_framework import status
from rest_framework.response import Response

from apps.common.exceptions import (
    BaseApplicationException,
    DuplicateResourceException,
    ResourceNotFoundException,
    ValidationException,
)
from apps.common.responses import error_response, success_response

from .models import RuleGroup
from .repositories import RuleRepository


class RuleService:
    """Service layer for Rule aggregate operations."""

    def __init__(self, repository: RuleRepository | None = None) -> None:
        self.repository = repository or RuleRepository()

    @staticmethod
    def _serialize(instance: Any) -> dict[str, Any]:
        data = model_to_dict(instance)
        data["id"] = str(instance.id)
        data["code"] = instance.code
        if getattr(instance, "rule_group_id", None):
            data["rule_group_id"] = str(instance.rule_group_id)
            rule_group = getattr(instance, "rule_group", None)
            if rule_group is not None:
                data["rule_group"] = {
                    "id": str(rule_group.id),
                    "code": rule_group.code,
                    "name": rule_group.name,
                    "priority": rule_group.priority,
                }
        else:
            data["rule_group_id"] = ""
            data["rule_group"] = None
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

    @staticmethod
    def _resolve_rule_group(data: dict[str, Any], *, for_update: bool = False) -> RuleGroup | None:
        rule_group_from_serializer = data.pop("rule_group", None)
        if rule_group_from_serializer is not None:
            return rule_group_from_serializer

        rule_group_id_raw = data.get("rule_group_id")
        if not rule_group_id_raw:
            return None if for_update else None

        try:
            rule_group_id = uuid.UUID(str(rule_group_id_raw))
        except (TypeError, ValueError) as exc:
            raise ValidationException(detail="Field 'rule_group_id' must be a valid UUID.") from exc

        rule_group = RuleGroup.all_objects.filter(id=rule_group_id).first()
        if rule_group:
            return rule_group

        generated_code = f"RULE_GRP_{str(rule_group_id).replace('-', '').upper()[:24]}"
        return RuleGroup.all_objects.create(
            id=rule_group_id,
            code=generated_code,
            name=f"Rule Group {str(rule_group_id)[:8]}",
            description="Auto-generated rule group for rule creation.",
            status=data.get("status") or "DRAFT",
        )

    def _prepare_create_update_payload(self, data: dict[str, Any], *, for_update: bool = False) -> dict[str, Any]:
        payload = dict(data)

        rule_group = self._resolve_rule_group(payload, for_update=for_update)
        if rule_group is not None:
            payload["rule_group"] = rule_group
        elif not for_update:
            raise ValidationException(detail="Field 'rule_group_id' is required.")

        if "rule_group_id" in payload:
            payload.pop("rule_group_id", None)

        return payload

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
            payload = self._prepare_create_update_payload(data, for_update=False)
            code = payload.get("code")
            if not code:
                raise ValidationException(detail="Field 'code' is required.")
            if self.repository.exists(code):
                raise DuplicateResourceException(detail=f"Resource with code '{code}' already exists.")
            instance = self.repository.create(payload)
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
            payload = self._prepare_create_update_payload(data, for_update=True)
            new_code = payload.get("code")
            if new_code:
                existing = self.repository.get_by_code(new_code)
                if existing and existing.id != instance.id:
                    raise DuplicateResourceException(detail=f"Resource with code '{new_code}' already exists.")
            updated = self.repository.update(instance, payload)
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
