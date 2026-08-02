from __future__ import annotations

import logging
from typing import Any

from django.contrib.auth import authenticate, update_session_auth_hash
from django.contrib.auth.models import update_last_login
from django.forms.models import model_to_dict
from rest_framework import status
from rest_framework.response import Response
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.serializers import TokenRefreshSerializer, TokenVerifySerializer
from rest_framework_simplejwt.tokens import AccessToken, RefreshToken

from apps.common.exceptions import (
    AuthenticationException,
    AuthorizationException,
    BaseApplicationException,
    BusinessRuleException,
    DuplicateResourceException,
    ResourceNotFoundException,
    ValidationException,
)
from apps.common.responses import error_response, success_response

from .repositories import (
    AuthenticationAuditRepository,
    AuthenticationRepository,
    IdentityRepository,
    PermissionCatalogRepository,
    PermissionRepository,
    UserDirectoryRepository,
)

logger = logging.getLogger(__name__)


class IdentityService:
    """Service layer for Identity aggregate operations."""

    def __init__(self, repository: IdentityRepository | None = None) -> None:
        self.repository = repository or IdentityRepository()

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

    def get_all(self) -> Response:
        try:
            records = [self._serialize(item) for item in self.repository.get_all()]
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


class PermissionCatalogService:
    """Service layer for Permission catalog CRUD operations."""

    def __init__(self, repository: PermissionCatalogRepository | None = None) -> None:
        self.repository = repository or PermissionCatalogRepository()

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


class UserDirectoryService:
    """Read-only service for enterprise user directory views."""

    def __init__(self, repository: UserDirectoryRepository | None = None) -> None:
        self.repository = repository or UserDirectoryRepository()

    @staticmethod
    def _serialize_user(user, *, roles: list[str], permissions: list[dict[str, str]]) -> dict[str, Any]:
        return {
            "id": str(user.id),
            "username": user.username,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "email": user.email,
            "is_active": user.is_active,
            "roles": roles,
            "permissions": permissions,
        }

    def get_all(self, query_params: dict[str, Any] | None = None) -> Response:
        users = self.repository.get_all(query_params=query_params)
        data = []
        for user in users:
            roles = self.repository.get_roles(user)
            permissions = self.repository.get_permissions(user)
            data.append(self._serialize_user(user, roles=roles, permissions=permissions))
        return success_response(data=data, message="Records fetched successfully.")


class AuthenticationAuditService:
    def __init__(self, repository: AuthenticationAuditRepository | None = None) -> None:
        self.repository = repository or AuthenticationAuditRepository()

    @staticmethod
    def _client_ip(request) -> str:
        x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR", "") if request else ""
        if x_forwarded_for:
            return x_forwarded_for.split(",")[0].strip()
        return request.META.get("REMOTE_ADDR", "") if request else ""

    @staticmethod
    def _user_agent(request) -> str:
        return (request.META.get("HTTP_USER_AGENT", "")[:512] if request else "")

    @staticmethod
    def _request_id(request) -> str:
        return str(getattr(request, "request_id", "") or "")

    def log_event(
        self,
        *,
        request,
        user,
        username: str,
        action: str,
        success: bool,
        description: str,
    ) -> None:
        try:
            outcome = "SUCCESS" if success else "FAILED"
            activity = f"{action.upper()}_{outcome}"
            reference_number = username or self._request_id(request)
            event_description = f"{description} | request_id={self._request_id(request)}"

            self.repository.log_activity(
                user=user,
                activity=activity,
                description=event_description,
                request_id=self._request_id(request),
                reference_number=reference_number,
            )

            entity_id = str(getattr(user, "id", "") or username or "anonymous")
            self.repository.log_audit(
                user=user,
                action=activity,
                entity_id=entity_id,
                description=description,
                ip_address=self._client_ip(request),
                user_agent=self._user_agent(request),
            )
        except Exception as exc:
            logger.warning("Failed to persist authentication audit event: %s", exc)


class AuthenticationService:
    def __init__(
        self,
        repository: AuthenticationRepository | None = None,
        audit_service: AuthenticationAuditService | None = None,
    ) -> None:
        self.repository = repository or AuthenticationRepository()
        self.audit_service = audit_service or AuthenticationAuditService()

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
    def _serialize_user(user, *, access_context: dict[str, Any], roles: list[str]) -> dict[str, Any]:
        return {
            "id": str(user.id),
            "username": user.username,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "email": user.email,
            "is_active": user.is_active,
            "is_staff": user.is_staff,
            "is_superuser": user.is_superuser,
            "last_login": user.last_login.isoformat() if user.last_login else None,
            "roles": roles,
            "permissions": access_context.get("permissions", []),
            "application": access_context.get("application", {}),
            "programs": access_context.get("programs", []),
        }

    @staticmethod
    def _build_token_pair(
        user,
        *,
        roles: list[str],
        access_context: dict[str, Any],
    ) -> dict[str, str]:
        refresh = RefreshToken.for_user(user)
        refresh["username"] = user.username
        refresh["roles"] = roles
        refresh["permissions"] = access_context.get("permissions", [])
        refresh["application"] = access_context.get("application", {})
        refresh["programs"] = access_context.get("programs", [])
        return {"refresh": str(refresh), "access": str(refresh.access_token)}

    def login(self, *, request, username: str, password: str) -> Response:
        try:
            username = (username or "").strip()
            if not username or not password:
                raise ValidationException(detail="Both username and password are required.")

            user = authenticate(request=request, username=username, password=password)
            if not user:
                failure_reason = getattr(request, "_auth_failure_reason", "Invalid username or password.")
                self.audit_service.log_event(
                    request=request,
                    user=None,
                    username=username,
                    action="LOGIN",
                    success=False,
                    description=failure_reason,
                )
                raise AuthenticationException(detail=failure_reason)

            access_context = self.repository.get_access_context(user)
            roles = self.repository.get_roles(user)
            tokens = self._build_token_pair(user, roles=roles, access_context=access_context)
            update_last_login(None, user)

            self.audit_service.log_event(
                request=request,
                user=user,
                username=user.username,
                action="LOGIN",
                success=True,
                description="User authenticated via BAUTHONE and JWT issued.",
            )

            return success_response(
                data={
                    "tokens": tokens,
                    "user": self._serialize_user(user, access_context=access_context, roles=roles),
                },
                message="Login successful.",
            )
        except BaseApplicationException as exc:
            return self._error(exc)

    def logout(self, *, request, refresh_token: str) -> Response:
        try:
            if not refresh_token:
                raise ValidationException(detail="Refresh token is required.")

            token = RefreshToken(refresh_token)
            token.blacklist()

            if getattr(request, "user", None) and request.user.is_authenticated:
                self.repository.clear_access_context(request.user)

            self.audit_service.log_event(
                request=request,
                user=getattr(request, "user", None),
                username=getattr(getattr(request, "user", None), "username", ""),
                action="LOGOUT",
                success=True,
                description="Refresh token blacklisted and user session revoked.",
            )

            return success_response(data={"logged_out": True}, message="Logout successful.")
        except TokenError as exc:
            self.audit_service.log_event(
                request=request,
                user=getattr(request, "user", None),
                username=getattr(getattr(request, "user", None), "username", ""),
                action="LOGOUT",
                success=False,
                description=f"Token blacklist failed: {exc}",
            )
            return self._error(ValidationException(detail="Invalid refresh token."))
        except BaseApplicationException as exc:
            return self._error(exc)

    def refresh_token(self, *, request, refresh_token: str) -> Response:
        try:
            if not refresh_token:
                raise ValidationException(detail="Refresh token is required.")

            serializer = TokenRefreshSerializer(data={"refresh": refresh_token})
            serializer.is_valid(raise_exception=True)

            payload = {
                "access": serializer.validated_data.get("access"),
                "refresh": serializer.validated_data.get("refresh", refresh_token),
            }
            return success_response(data=payload, message="Token refreshed successfully.")
        except TokenError:
            return self._error(ValidationException(detail="Invalid refresh token."))
        except Exception as exc:
            logger.warning("Token refresh failed: %s", exc)
            return self._error(ValidationException(detail="Token refresh failed."))

    def verify_token(self, *, token: str) -> Response:
        try:
            if not token:
                raise ValidationException(detail="Token is required.")

            serializer = TokenVerifySerializer(data={"token": token})
            serializer.is_valid(raise_exception=True)
            decoded = AccessToken(token)

            return success_response(
                data={
                    "valid": True,
                    "token_type": decoded.get("token_type"),
                    "user_id": decoded.get("user_id"),
                    "expires_at": decoded.get("exp"),
                },
                message="Token is valid.",
            )
        except TokenError:
            return self._error(AuthenticationException(detail="Invalid token."))
        except Exception as exc:
            logger.warning("Token verification failed: %s", exc)
            return self._error(AuthenticationException(detail="Invalid token."))

    def get_current_user(self, *, user) -> Response:
        try:
            if not user or not user.is_authenticated:
                raise AuthenticationException(detail="Authentication is required.")

            access_context = self.repository.get_access_context(user)
            roles = self.repository.get_roles(user)
            return success_response(
                data=self._serialize_user(user, access_context=access_context, roles=roles),
                message="User profile fetched successfully.",
            )
        except BaseApplicationException as exc:
            return self._error(exc)

    def update_current_user(self, *, user, profile_data: dict[str, Any]) -> Response:
        try:
            if not user or not user.is_authenticated:
                raise AuthenticationException(detail="Authentication is required.")

            updated_user = self.repository.update_user_profile(user, profile_data)
            access_context = self.repository.get_access_context(updated_user)
            roles = self.repository.get_roles(updated_user)

            return success_response(
                data=self._serialize_user(updated_user, access_context=access_context, roles=roles),
                message="Profile updated successfully.",
            )
        except BaseApplicationException as exc:
            return self._error(exc)

    def change_password(
        self,
        *,
        request,
        user,
        current_password: str,
        new_password: str,
    ) -> Response:
        try:
            if not user or not user.is_authenticated:
                raise AuthenticationException(detail="Authentication is required.")
            if not user.has_usable_password():
                raise BusinessRuleException(
                    detail="Password is managed by Active Directory and cannot be changed here."
                )
            if not user.check_password(current_password):
                raise AuthenticationException(detail="Current password is incorrect.")
            if current_password == new_password:
                raise ValidationException(detail="New password must be different from current password.")

            self.repository.update_password(user, new_password)
            update_session_auth_hash(request, user)

            self.audit_service.log_event(
                request=request,
                user=user,
                username=user.username,
                action="CHANGE_PASSWORD",
                success=True,
                description="User changed account password successfully.",
            )

            return success_response(data={"changed": True}, message="Password changed successfully.")
        except BaseApplicationException as exc:
            return self._error(exc)

    def get_roles(self, *, user) -> Response:
        try:
            if not user or not user.is_authenticated:
                raise AuthenticationException(detail="Authentication is required.")
            return success_response(data=self.repository.get_roles(user), message="Roles fetched successfully.")
        except BaseApplicationException as exc:
            return self._error(exc)

    def get_permissions(self, *, user) -> Response:
        try:
            if not user or not user.is_authenticated:
                raise AuthenticationException(detail="Authentication is required.")
            access_context = self.repository.get_access_context(user)
            return success_response(
                data=access_context.get("permissions", []),
                message="Permissions fetched successfully.",
            )
        except BaseApplicationException as exc:
            return self._error(exc)


class PermissionService:
    def __init__(self, repository: PermissionRepository | None = None) -> None:
        self.repository = repository or PermissionRepository()

    def has_permission(self, *, user, module: str, action: str) -> bool:
        return self.repository.has_permission(user, module, action)

    def has_role(self, *, user, role_name: str) -> bool:
        return self.repository.has_role(user, role_name)

    def has_program_access(
        self,
        *,
        user,
        program_code: str,
        module_name: str | None = None,
        application_name: str | None = None,
    ) -> bool:
        return self.repository.has_program_access(
            user,
            program_code,
            module_name=module_name,
            application_name=application_name,
        )

    def has_operation(
        self,
        *,
        user,
        program_code: str,
        operation_name: str,
        module_name: str | None = None,
        application_name: str | None = None,
    ) -> bool:
        return self.repository.has_operation(
            user,
            program_code=program_code,
            operation_name=operation_name,
            module_name=module_name,
            application_name=application_name,
        )

    def ensure_permission(self, *, user, module: str, action: str) -> None:
        if not self.has_permission(user=user, module=module, action=action):
            raise AuthorizationException(detail="Permission denied.")

    def ensure_role(self, *, user, role_name: str) -> None:
        if not self.has_role(user=user, role_name=role_name):
            raise AuthorizationException(detail="Role check failed.")
