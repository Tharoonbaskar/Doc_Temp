from __future__ import annotations

from typing import Any

from rest_framework import status
from rest_framework.exceptions import APIException
from rest_framework.views import exception_handler

from .responses import error_response


class BaseApplicationException(APIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = "Application error."
    default_code = "application_error"

    def __init__(
        self,
        detail: Any = None,
        code: str | None = None,
        *,
        errors: dict[str, Any] | list[Any] | None = None,
    ) -> None:
        self.errors = errors or {}
        super().__init__(detail=detail, code=code)


class ValidationException(BaseApplicationException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = "Validation failed."
    default_code = "validation_error"


class BusinessRuleException(BaseApplicationException):
    status_code = status.HTTP_422_UNPROCESSABLE_ENTITY
    default_detail = "Business rule violation."
    default_code = "business_rule_error"


class ResourceNotFoundException(BaseApplicationException):
    status_code = status.HTTP_404_NOT_FOUND
    default_detail = "Requested resource was not found."
    default_code = "resource_not_found"


class DuplicateResourceException(BaseApplicationException):
    status_code = status.HTTP_409_CONFLICT
    default_detail = "Duplicate resource detected."
    default_code = "duplicate_resource"


class AuthenticationException(BaseApplicationException):
    status_code = status.HTTP_401_UNAUTHORIZED
    default_detail = "Authentication failed."
    default_code = "authentication_failed"


class AuthorizationException(BaseApplicationException):
    status_code = status.HTTP_403_FORBIDDEN
    default_detail = "You do not have permission to perform this action."
    default_code = "authorization_failed"


class ExternalServiceException(BaseApplicationException):
    status_code = status.HTTP_502_BAD_GATEWAY
    default_detail = "External service request failed."
    default_code = "external_service_error"


def _normalize_error_payload(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key): _normalize_error_payload(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_normalize_error_payload(item) for item in value]
    return str(value)


def enterprise_exception_handler(exc: Exception, context: dict[str, Any]):
    if isinstance(exc, BaseApplicationException):
        detail = exc.detail
        message = detail if isinstance(detail, str) else str(exc.default_detail)
        errors = exc.errors if getattr(exc, "errors", None) else _normalize_error_payload(detail)
        return error_response(
            message=message,
            errors=errors,
            status_code=exc.status_code,
            error_code=getattr(exc, "default_code", "application_error"),
        )

    response = exception_handler(exc, context)
    if response is None:
        return error_response(
            message="An unexpected error occurred.",
            errors=[],
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            error_code="internal_server_error",
        )

    payload = response.data
    message = "Request failed."
    if isinstance(payload, dict) and payload.get("detail"):
        message = str(payload["detail"])
    elif response.status_code == status.HTTP_400_BAD_REQUEST:
        message = "Validation failed."
    elif isinstance(payload, str):
        message = payload

    default_code = getattr(exc, "default_code", None)
    error_code = str(default_code) if default_code else None

    return error_response(
        message=message,
        errors=_normalize_error_payload(payload),
        status_code=response.status_code,
        error_code=error_code,
    )