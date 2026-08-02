from __future__ import annotations

from typing import Any

from apps.common.exceptions import AuthenticationException, AuthorizationException
from apps.identity.repositories import AuthenticationRepository
from apps.identity.services import PermissionService


class RuntimeAuthorizationService:
    """Enterprise authorization checks for runtime APIs."""

    ACTION_POLICIES: dict[str, dict[str, Any]] = {
        "preview": {
            "operation_candidates": ["PREVIEW", "VIEW"],
            "permission_actions": ["preview", "view"],
        },
        "generate": {
            "operation_candidates": ["GENERATE", "MODIFY", "ADD"],
            "permission_actions": ["generate", "modify", "add"],
        },
        "status": {
            "operation_candidates": ["STATUS", "VIEW"],
            "permission_actions": ["status", "view"],
        },
        "download": {
            "operation_candidates": ["DOWNLOAD", "VIEW"],
            "permission_actions": ["download", "view"],
        },
        "history": {
            "operation_candidates": ["HISTORY", "VIEW"],
            "permission_actions": ["history", "view"],
        },
    }

    def __init__(
        self,
        permission_service: PermissionService | None = None,
        auth_repository: AuthenticationRepository | None = None,
    ) -> None:
        self.permission_service = permission_service or PermissionService()
        self.auth_repository = auth_repository or AuthenticationRepository()

    @staticmethod
    def _normalize_action(action: str) -> str:
        value = (action or "").strip().lower()
        if value not in RuntimeAuthorizationService.ACTION_POLICIES:
            raise AuthorizationException(detail=f"Unsupported authorization action '{action}'.")
        return value

    @staticmethod
    def _pick_program_code(data: dict[str, Any], access_context: dict[str, Any]) -> str:
        payload_program_code = str(data.get("program_code") or "").strip()
        if payload_program_code:
            return payload_program_code

        programs = access_context.get("programs") or []
        for item in programs:
            program_code = str(item.get("program_code") or "").strip()
            if program_code:
                return program_code

        return ""

    @staticmethod
    def _has_permission_action(
        access_context: dict[str, Any],
        action_candidates: list[str],
    ) -> bool:
        expected = {item.strip().lower() for item in action_candidates if item.strip()}
        if not expected:
            return False

        permissions = access_context.get("permissions") or []
        for item in permissions:
            permission_action = str(item.get("action") or "").strip().lower()
            if permission_action in expected:
                return True
        return False

    def authorize(self, *, request, action: str, data: dict[str, Any] | None = None) -> dict[str, Any]:
        user = getattr(request, "user", None)
        if not user or not user.is_authenticated:
            raise AuthenticationException(detail="JWT authentication is required.")

        normalized_action = self._normalize_action(action)
        policy = self.ACTION_POLICIES[normalized_action]

        roles = self.auth_repository.get_roles(user)
        if not roles:
            raise AuthorizationException(detail="Role validation failed for runtime operation.")

        access_context = self.auth_repository.get_access_context(user)
        if not (access_context.get("programs") or []):
            raise AuthorizationException(detail="Program validation failed for runtime operation.")

        payload = data or {}
        module_name = str(payload.get("module_name") or "").strip() or None
        application_name = str(payload.get("application_name") or "").strip() or None
        program_code = self._pick_program_code(payload, access_context)
        if not program_code:
            raise AuthorizationException(detail="Program validation failed for runtime operation.")

        if not self.permission_service.has_program_access(
            user=user,
            program_code=program_code,
            module_name=module_name,
            application_name=application_name,
        ):
            raise AuthorizationException(detail="Program access denied.")

        operation_candidates = [str(item).strip().upper() for item in policy["operation_candidates"]]
        operation_passed = False
        operation_used = ""
        for candidate in operation_candidates:
            if self.permission_service.has_operation(
                user=user,
                program_code=program_code,
                operation_name=candidate,
                module_name=module_name,
                application_name=application_name,
            ):
                operation_passed = True
                operation_used = candidate
                break
        if not operation_passed:
            raise AuthorizationException(detail="Operation access denied.")

        permission_actions = [str(item).strip().lower() for item in policy["permission_actions"]]
        permission_passed = any(
            self.permission_service.has_permission(user=user, module="runtime", action=item)
            for item in permission_actions
        )
        if not permission_passed:
            permission_passed = self._has_permission_action(access_context, permission_actions)

        if not permission_passed:
            raise AuthorizationException(detail="Permission validation failed for runtime operation.")

        return {
            "roles": roles,
            "program_code": program_code,
            "operation": operation_used,
            "permission_actions": permission_actions,
        }
