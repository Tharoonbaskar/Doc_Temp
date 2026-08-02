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

from .repositories import DocumentDefinitionRepository, DocumentRepository
from .models import DocumentCategory


class DocumentService:
    """Service layer for Document aggregate operations."""

    def __init__(self, repository: DocumentRepository | None = None) -> None:
        self.repository = repository or DocumentRepository()

    @staticmethod
    def _serialize(instance: Any) -> dict[str, Any]:
        data = model_to_dict(instance)
        data["id"] = str(instance.id)
        data["code"] = instance.code
        if getattr(instance, "category_id", None):
            data["category_id"] = str(instance.category_id)
            category = getattr(instance, "category", None)
            if category is not None:
                data["category"] = {
                    "id": str(category.id),
                    "code": category.code,
                    "name": category.name,
                }
        else:
            data["category_id"] = ""
            data["category"] = None

        product_value = data.get("product")
        if isinstance(product_value, str):
            data["product"] = [item.strip() for item in product_value.split(",") if item.strip()]
        elif isinstance(product_value, list):
            data["product"] = product_value
        else:
            data["product"] = []

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
    def _product_to_db_value(product_value: Any) -> str:
        if isinstance(product_value, list):
            return ", ".join(item.strip() for item in product_value if isinstance(item, str) and item.strip())
        if isinstance(product_value, str):
            return product_value.strip()
        return ""

    @staticmethod
    def _resolve_category(data: dict[str, Any], *, for_update: bool = False) -> DocumentCategory | None:
        category_from_serializer = data.pop("category", None)
        if category_from_serializer is not None:
            return category_from_serializer

        category_id_raw = data.get("category_id")
        if not category_id_raw:
            return None if for_update else None

        try:
            category_id = uuid.UUID(str(category_id_raw))
        except (TypeError, ValueError) as exc:
            raise ValidationException(detail="Field 'category_id' must be a valid UUID.") from exc

        category = DocumentCategory.all_objects.filter(id=category_id).first()
        if category:
            return category

        generated_code = f"DOC_CAT_{str(category_id).replace('-', '').upper()[:24]}"
        return DocumentCategory.all_objects.create(
            id=category_id,
            code=generated_code,
            name=f"Document Category {str(category_id)[:8]}",
            description="Auto-generated category for document creation.",
            status=data.get("status") or "DRAFT",
        )

    def _prepare_create_update_payload(self, data: dict[str, Any], *, for_update: bool = False) -> dict[str, Any]:
        payload = dict(data)

        category = self._resolve_category(payload, for_update=for_update)
        if category is not None:
            payload["category"] = category
        elif not for_update:
            raise ValidationException(detail="Field 'category_id' is required.")

        if "category_id" in payload:
            payload.pop("category_id", None)

        if "product" in payload:
            payload["product"] = self._product_to_db_value(payload.get("product"))

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


class DocumentDefinitionService:
    """Service layer for DocumentDefinition aggregate operations."""

    def __init__(self, repository: DocumentDefinitionRepository | None = None) -> None:
        self.repository = repository or DocumentDefinitionRepository()

    @staticmethod
    def _serialize(instance: Any) -> dict[str, Any]:
        data = model_to_dict(instance)
        data["id"] = str(instance.id)
        data["code"] = instance.code
        if getattr(instance, "document_id", None):
            data["document_id"] = str(instance.document_id)
            document = getattr(instance, "document", None)
            if document is not None:
                data["document"] = {
                    "id": str(document.id),
                    "code": document.code,
                    "name": document.name,
                    "document_type": document.document_type,
                    "output_format": document.output_format,
                }
        else:
            data["document_id"] = ""
            data["document"] = None
        data["status"] = instance.status
        data["is_deleted"] = instance.is_deleted
        data["created_at"] = instance.created_at.isoformat() if instance.created_at else None
        data["updated_at"] = instance.updated_at.isoformat() if instance.updated_at else None
        data["deleted_at"] = instance.deleted_at.isoformat() if instance.deleted_at else None
        data["effective_from"] = instance.effective_from.isoformat() if instance.effective_from else None
        data["effective_to"] = instance.effective_to.isoformat() if instance.effective_to else None
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
