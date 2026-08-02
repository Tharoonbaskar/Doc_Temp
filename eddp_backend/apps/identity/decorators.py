from __future__ import annotations

from functools import wraps
from typing import Any, Callable

from rest_framework import status

from apps.common.responses import error_response

from .services import PermissionService


def _resolve_request(args: tuple[Any, ...], kwargs: dict[str, Any]):
    request = kwargs.get("request")
    if request is not None:
        return request

    if not args:
        return None

    first = args[0]
    if hasattr(first, "META") and hasattr(first, "user"):
        return first

    if len(args) > 1:
        second = args[1]
        if hasattr(second, "META") and hasattr(second, "user"):
            return second

    return None


def _forbidden(message: str):
    return error_response(
        message=message,
        errors=[],
        status_code=status.HTTP_403_FORBIDDEN,
        error_code="authorization_failed",
    )


def program_required(program_code: str, module_name: str | None = None, application_name: str | None = None):
    def decorator(func: Callable):
        @wraps(func)
        def wrapper(*args, **kwargs):
            request = _resolve_request(args, kwargs)
            user = getattr(request, "user", None)
            service = PermissionService()
            has_access = service.has_program_access(
                user=user,
                program_code=program_code,
                module_name=module_name,
                application_name=application_name,
            )
            if not has_access:
                return _forbidden("Program access denied.")
            return func(*args, **kwargs)

        return wrapper

    return decorator


def permission_required(module: str, action: str):
    def decorator(func: Callable):
        @wraps(func)
        def wrapper(*args, **kwargs):
            request = _resolve_request(args, kwargs)
            user = getattr(request, "user", None)
            service = PermissionService()
            has_access = service.has_permission(user=user, module=module, action=action)
            if not has_access:
                return _forbidden("Permission denied.")
            return func(*args, **kwargs)

        return wrapper

    return decorator


def operation_required(
    program_code: str,
    operation_name: str,
    module_name: str | None = None,
    application_name: str | None = None,
):
    def decorator(func: Callable):
        @wraps(func)
        def wrapper(*args, **kwargs):
            request = _resolve_request(args, kwargs)
            user = getattr(request, "user", None)
            service = PermissionService()
            has_access = service.has_operation(
                user=user,
                program_code=program_code,
                operation_name=operation_name,
                module_name=module_name,
                application_name=application_name,
            )
            if not has_access:
                return _forbidden("Operation access denied.")
            return func(*args, **kwargs)

        return wrapper

    return decorator
