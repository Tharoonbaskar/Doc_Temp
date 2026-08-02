from __future__ import annotations

from typing import Any

from rest_framework import status
from rest_framework.response import Response


def success_response(
    data: Any = None,
    message: str = "Request successful.",
    *,
    status_code: int = status.HTTP_200_OK,
    meta: dict[str, Any] | None = None,
) -> Response:
    payload: dict[str, Any] = {
        "success": True,
        "message": message,
        "data": data,
    }
    if meta is not None:
        payload["meta"] = meta
    return Response(payload, status=status_code)


def error_response(
    message: str = "Request failed.",
    *,
    errors: Any = None,
    status_code: int = status.HTTP_400_BAD_REQUEST,
    error_code: str | None = None,
) -> Response:
    payload: dict[str, Any] = {
        "success": False,
        "message": message,
        "errors": errors if errors is not None else [],
    }
    if error_code is not None:
        payload["error_code"] = error_code
    return Response(payload, status=status_code)


def paginated_response(
    *,
    data: Any,
    count: int,
    next_link: str | None,
    previous_link: str | None,
    page: int,
    page_size: int,
    message: str = "Request successful.",
    status_code: int = status.HTTP_200_OK,
    extra_meta: dict[str, Any] | None = None,
) -> Response:
    meta: dict[str, Any] = {
        "pagination": {
            "count": count,
            "next": next_link,
            "previous": previous_link,
            "page": page,
            "page_size": page_size,
        }
    }
    if extra_meta:
        meta.update(extra_meta)
    return success_response(data=data, message=message, status_code=status_code, meta=meta)