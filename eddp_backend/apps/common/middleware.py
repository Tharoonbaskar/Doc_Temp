from __future__ import annotations

from typing import Callable

from django.http import HttpRequest, HttpResponse


class DeprecatedEndpointHeadersMiddleware:
    """Attach deprecation metadata for legacy nested API endpoints."""

    LEGACY_ENDPOINT_SUCCESSORS = {
        "/api/documents/documents": "/api/documents/",
        "/api/templates/templates": "/api/templates/",
        "/api/variables/variables": "/api/variables/",
        "/api/connectors/connectors": "/api/connectors/",
        "/api/rules/rules": "/api/generation-rules/",
        "/api/workflow/workflows": "/api/workflow/",
    }
    SUNSET = "Tue, 31 Mar 2027 23:59:59 GMT"

    def __init__(self, get_response: Callable[[HttpRequest], HttpResponse]) -> None:
        self.get_response = get_response

    @classmethod
    def _resolve_successor(cls, path: str) -> tuple[str, str] | None:
        normalized = path.rstrip("/") or "/"
        for legacy_endpoint, successor_endpoint in cls.LEGACY_ENDPOINT_SUCCESSORS.items():
            if normalized == legacy_endpoint or normalized.startswith(f"{legacy_endpoint}/"):
                return legacy_endpoint, successor_endpoint
        return None

    def __call__(self, request: HttpRequest) -> HttpResponse:
        response = self.get_response(request)
        matched = self._resolve_successor(request.path)
        if matched is None:
            return response

        legacy_endpoint, successor_endpoint = matched
        response["Deprecation"] = "true"
        response["Sunset"] = self.SUNSET
        response["Link"] = f"<{successor_endpoint}>; rel=\"successor-version\""
        response["X-Deprecated-Endpoint"] = legacy_endpoint
        return response
