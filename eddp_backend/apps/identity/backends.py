from __future__ import annotations

import logging
from typing import Any

import requests
from django.conf import settings
from django.contrib.auth.backends import BaseBackend
from django.contrib.auth import get_user_model

from .repositories import AuthenticationRepository

logger = logging.getLogger(__name__)


class EnterpriseAuthenticationBackend(BaseBackend):
    """Authenticate users against BAUTHONE and synchronize enterprise authorization context."""

    def __init__(self) -> None:
        self.repository = AuthenticationRepository()

    @staticmethod
    def _extract_role_names(raw_roles: list[Any]) -> list[str]:
        role_names: list[str] = []
        for role in raw_roles:
            if isinstance(role, str):
                if role.strip():
                    role_names.append(role.strip())
                continue
            if isinstance(role, dict):
                candidate = (
                    role.get("roleName")
                    or role.get("name")
                    or role.get("role")
                    or role.get("code")
                    or ""
                )
                if str(candidate).strip():
                    role_names.append(str(candidate).strip())
        return sorted(set(role_names))

    @staticmethod
    def _extract_operation_name(item: Any) -> str:
        if isinstance(item, str):
            return item.strip()
        if isinstance(item, dict):
            return (
                str(item.get("operationName") or item.get("name") or item.get("operation") or "")
                .strip()
            )
        return ""

    @staticmethod
    def _extract_permissions_from_operation(module_name: str, operation: Any) -> list[dict[str, str]]:
        operation_name = EnterpriseAuthenticationBackend._extract_operation_name(operation)
        if not operation_name:
            return []

        permissions: list[dict[str, str]] = [
            {
                "module": module_name,
                "action": operation_name,
                "description": f"{module_name} - {operation_name}",
            }
        ]

        if isinstance(operation, dict):
            explicit_permissions = operation.get("permissions") or operation.get("permission") or []
            if isinstance(explicit_permissions, str):
                explicit_permissions = [explicit_permissions]
            if isinstance(explicit_permissions, list):
                for permission in explicit_permissions:
                    permission_name = str(permission or "").strip()
                    if not permission_name:
                        continue
                    permissions.append(
                        {
                            "module": module_name,
                            "action": permission_name,
                            "description": f"{module_name} - {permission_name}",
                        }
                    )

        return permissions

    @staticmethod
    def _is_success(payload: dict[str, Any]) -> bool:
        status_value = payload.get("status")
        success_value = payload.get("success")
        if isinstance(success_value, bool):
            return success_value
        if isinstance(status_value, bool):
            return status_value
        return str(status_value or "").strip().lower() in {"success", "ok", "allowed"}

    @staticmethod
    def _is_access_allowed(payload: dict[str, Any]) -> bool:
        app_details = payload.get("appDtls") or {}
        access_value = app_details.get("access")
        if access_value is None:
            return True
        return str(access_value).strip().lower() in {"allowed", "true", "yes", "success"}

    @staticmethod
    def _resolve_app_name(payload: dict[str, Any]) -> str:
        app_details = payload.get("appDtls") or {}
        return str(app_details.get("appName") or payload.get("appName") or "").strip()

    def _build_access_context(self, payload: dict[str, Any]) -> dict[str, Any]:
        app_details = payload.get("appDtls") or {}
        app_name = self._resolve_app_name(payload)
        modules_data = app_details.get("programs") or payload.get("programs") or []
        role_names = self._extract_role_names(payload.get("roles") or app_details.get("roles") or [])

        programs: list[dict[str, Any]] = []
        permissions: list[dict[str, str]] = []

        for module in modules_data:
            module_name = str(module.get("moduleName") or module.get("module") or "").strip() or "General"
            module_programs = module.get("programs") or []

            for program in module_programs:
                program_code = str(program.get("programCode") or program.get("code") or "").strip()
                if not program_code:
                    continue
                program_name = str(program.get("programName") or program.get("name") or "").strip()

                operation_items = program.get("operations") or []
                operation_names: list[str] = []

                for operation in operation_items:
                    operation_name = self._extract_operation_name(operation)
                    if not operation_name:
                        continue
                    operation_names.append(operation_name)
                    permissions.extend(self._extract_permissions_from_operation(module_name, operation))

                programs.append(
                    {
                        "application": app_name,
                        "module": module_name,
                        "program_code": program_code,
                        "program_name": program_name,
                        "operations": sorted(set(operation_names)),
                    }
                )

        unique_permissions: list[dict[str, str]] = []
        seen_keys: set[tuple[str, str]] = set()
        for permission in permissions:
            key = (
                str(permission.get("module", "")).strip().lower(),
                str(permission.get("action", "")).strip().lower(),
            )
            if not key[0] or not key[1] or key in seen_keys:
                continue
            seen_keys.add(key)
            unique_permissions.append(permission)

        if not role_names:
            role_names = ["Enterprise User"]

        return {
            "application": {
                "name": app_name,
                "access": (app_details.get("access") or "allowed"),
            },
            "roles": role_names,
            "programs": programs,
            "permissions": unique_permissions,
        }

    @staticmethod
    def _is_superuser(access_context: dict[str, Any]) -> bool:
        privileged_operations = {"ADMIN", "SUPERUSER", "MODIFY"}
        for program in access_context.get("programs") or []:
            operations = {str(operation).upper() for operation in (program.get("operations") or [])}
            if operations.intersection(privileged_operations):
                return True
        return False

    @staticmethod
    def _mark_failure(request, message: str) -> None:
        if request is not None:
            setattr(request, "_auth_failure_reason", message)

    def _post(self, endpoint: str, payload: dict[str, Any]) -> dict[str, Any]:
        headers = {"Content-Type": "application/json"}
        response = requests.post(
            endpoint,
            json=payload,
            headers=headers,
            timeout=getattr(settings, "BAUTHONE_TIMEOUT", 15),
        )
        response.raise_for_status()
        data = response.json()
        if not isinstance(data, dict):
            raise ValueError("BAUTHONE response payload must be a JSON object.")
        return data

    def authenticate(self, request, username=None, password=None, **kwargs):
        if not username or not password:
            return None

        base_url = str(getattr(settings, "BAUTHONE_URL", "http://bauthone")).rstrip("/")
        auth_endpoint = f"{base_url}/api/usr/ad/check"
        program_endpoint = f"{base_url}/api/app/usr/programaccess"

        try:
            logger.info("BAUTHONE auth started for user '%s'.", username)

            auth_payload = {"userName": username, "passWord": password}
            auth_response = self._post(auth_endpoint, auth_payload)

            if not self._is_success(auth_response):
                self._mark_failure(request, "Active Directory authentication failed.")
                logger.warning("BAUTHONE AD validation failed for user '%s'.", username)
                return None

            employee_details = auth_response.get("userData") or auth_response.get("data") or {}

            program_payload = {
                "userName": username,
                "secretKey": getattr(settings, "BAUTHONE_SECRET_KEY", ""),
            }
            program_response = self._post(program_endpoint, program_payload)

            if not self._is_success(program_response):
                self._mark_failure(request, "Program access retrieval failed from BAUTHONE.")
                logger.warning("BAUTHONE program access status failed for user '%s'.", username)
                return None
            if not self._is_access_allowed(program_response):
                self._mark_failure(request, "User does not have access to this application.")
                logger.warning("Program access denied for user '%s'.", username)
                return None

            access_context = self._build_access_context(program_response)
            if not access_context.get("programs"):
                self._mark_failure(request, "No program access configured for this user.")
                logger.warning("No program access configured for user '%s'.", username)
                return None

            synchronized_permissions = self.repository.sync_permissions(access_context.get("permissions") or [])
            access_context["permissions"] = synchronized_permissions

            user = self.repository.upsert_user_from_bauthone(
                username=username,
                employee_details=employee_details,
                is_staff=True,
                is_superuser=self._is_superuser(access_context),
            )

            synchronized_roles = self.repository.sync_user_roles(user, access_context.get("roles") or [])
            access_context["roles"] = synchronized_roles
            self.repository.set_access_context(user, access_context)

            setattr(user, "_bauthone_access_context", access_context)
            logger.info("BAUTHONE auth succeeded for user '%s'.", username)
            return user
        except requests.exceptions.Timeout:
            self._mark_failure(request, "BAUTHONE authentication service timed out.")
            logger.error("BAUTHONE timeout while authenticating user '%s'.", username)
            return None
        except requests.exceptions.RequestException as exc:
            self._mark_failure(request, "BAUTHONE authentication service unavailable.")
            logger.error("BAUTHONE request failed for user '%s': %s", username, exc)
            return None
        except Exception as exc:
            self._mark_failure(request, "Unexpected authentication failure.")
            logger.error("Unexpected BAUTHONE auth error for user '%s': %s", username, exc)
            return None

    def get_user(self, user_id):
        user_model = get_user_model()
        try:
            return user_model.objects.get(pk=user_id)
        except user_model.DoesNotExist:
            return None
