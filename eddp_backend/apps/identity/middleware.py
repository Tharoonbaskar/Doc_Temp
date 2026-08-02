from __future__ import annotations

import json
import logging
import uuid

from rest_framework_simplejwt.tokens import AccessToken

from .repositories import AuthenticationRepository
from .services import AuthenticationAuditService

logger = logging.getLogger(__name__)


class EnterpriseAuthenticationMiddleware:
    """Adds request context, request-id tracking, and enterprise auth event auditing."""

    def __init__(self, get_response):
        self.get_response = get_response
        self.audit_service = AuthenticationAuditService()
        self.auth_repository = AuthenticationRepository()

    @staticmethod
    def _extract_bearer_token(request) -> str:
        auth_header = request.META.get("HTTP_AUTHORIZATION", "")
        if not auth_header:
            return ""
        parts = auth_header.split(" ", 1)
        if len(parts) != 2 or parts[0].strip().lower() != "bearer":
            return ""
        return parts[1].strip()

    @staticmethod
    def _safe_request_json(request) -> dict:
        try:
            raw_body = request.body
        except Exception:
            return {}

        if not raw_body:
            return {}

        try:
            if isinstance(raw_body, bytes):
                raw_body = raw_body.decode("utf-8")
            return json.loads(raw_body)
        except Exception:
            return {}

    def _set_request_context(self, request) -> None:
        request_id = str(uuid.uuid4())
        request.request_id = request_id
        request.user_context = {
            "request_id": request_id,
            "is_authenticated": False,
            "user_id": None,
            "username": "",
            "roles": [],
            "permissions": [],
            "application": {},
            "programs": [],
        }

        token = self._extract_bearer_token(request)
        if not token:
            return

        try:
            access_token = AccessToken(token)
            context = {
                "is_authenticated": True,
                "user_id": access_token.get("user_id"),
                "username": access_token.get("username", ""),
                "roles": access_token.get("roles", []),
                "permissions": access_token.get("permissions", []),
                "application": access_token.get("application", {}),
                "programs": access_token.get("programs", []),
            }
            request.user_context.update(context)
            user_id = context.get("user_id")
            if user_id:
                self.auth_repository.set_access_context(user_id, context)
        except Exception as exc:
            logger.debug("Unable to decode request JWT in middleware: %s", exc)

    def _audit_auth_endpoint(self, request, response) -> None:
        path = request.path.rstrip("/")
        if request.method.upper() != "POST":
            return

        if path.endswith("/api/auth/login"):
            payload = self._safe_request_json(request)
            username = str(payload.get("username") or payload.get("userName") or "").strip()
            self.audit_service.log_event(
                request=request,
                user=None,
                username=username,
                action="LOGIN",
                success=response.status_code < 400,
                description="Middleware login audit event.",
            )
            return

        if path.endswith("/api/auth/logout"):
            user = getattr(request, "user", None)
            username = getattr(user, "username", "") if user is not None else ""
            self.audit_service.log_event(
                request=request,
                user=user,
                username=username,
                action="LOGOUT",
                success=response.status_code < 400,
                description="Middleware logout audit event.",
            )

    def __call__(self, request):
        self._set_request_context(request)
        response = self.get_response(request)

        request_id = getattr(request, "request_id", "")
        if request_id:
            response["X-Request-ID"] = request_id

        try:
            self._audit_auth_endpoint(request, response)
        except Exception as exc:
            logger.warning("Authentication middleware audit failed: %s", exc)

        return response
