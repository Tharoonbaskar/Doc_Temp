from __future__ import annotations

import uuid
from typing import Any, Iterable

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.db import transaction
from django.db.models import Q, Prefetch, QuerySet
from django.utils.text import slugify

from apps.common.choices import StatusChoices

from .models import Permission, Role, UserRole


def _generate_code(prefix: str) -> str:
    return f"{prefix}-{uuid.uuid4().hex[:12].upper()}"


class IdentityRepository:
    model = Role

    def get_all(self) -> QuerySet[Role]:
        return self.model.objects.all()

    def get_by_id(self, id: Any) -> Role | None:
        return self.model.objects.filter(id=id).first()

    def get_by_code(self, code: str) -> Role | None:
        return self.model.objects.filter(code=code).first()

    @transaction.atomic
    def create(self, data: dict[str, Any]) -> Role:
        return self.model.objects.create(**data)

    @transaction.atomic
    def update(self, instance: Role, data: dict[str, Any]) -> Role:
        for field, value in data.items():
            setattr(instance, field, value)
        if data:
            instance.save(update_fields=list(data.keys()))
        else:
            instance.save()
        return instance

    @transaction.atomic
    def soft_delete(self, instance: Role) -> Role:
        instance.soft_delete()
        return instance

    @transaction.atomic
    def restore(self, instance: Role) -> Role:
        instance.restore()
        return instance

    def exists(self, code: str) -> bool:
        return self.model.objects.filter(code=code).exists()


class PermissionCatalogRepository:
    model = Permission

    def get_all(self, query_params: dict[str, Any] | None = None) -> QuerySet[Permission]:
        queryset = self.model.objects.all()
        params = query_params or {}

        status = (params.get("status") or "").strip()
        if status:
            queryset = queryset.filter(status__iexact=status)

        module = (params.get("module") or "").strip()
        if module:
            queryset = queryset.filter(module__icontains=module)

        action = (params.get("action") or "").strip()
        if action:
            queryset = queryset.filter(action__icontains=action)

        search = (params.get("search") or "").strip()
        if search:
            queryset = queryset.filter(
                Q(code__icontains=search)
                | Q(module__icontains=search)
                | Q(action__icontains=search)
                | Q(description__icontains=search)
            )

        return queryset

    def get_by_id(self, id: Any) -> Permission | None:
        return self.model.objects.filter(id=id).first()

    def get_by_code(self, code: str) -> Permission | None:
        return self.model.objects.filter(code=code).first()

    @transaction.atomic
    def create(self, data: dict[str, Any]) -> Permission:
        return self.model.objects.create(**data)

    @transaction.atomic
    def update(self, instance: Permission, data: dict[str, Any]) -> Permission:
        for field, value in data.items():
            setattr(instance, field, value)
        if data:
            instance.save(update_fields=list(data.keys()))
        else:
            instance.save()
        return instance

    @transaction.atomic
    def soft_delete(self, instance: Permission) -> Permission:
        instance.soft_delete()
        return instance

    @transaction.atomic
    def restore(self, instance: Permission) -> Permission:
        instance.restore()
        return instance

    def exists(self, code: str) -> bool:
        return self.model.objects.filter(code=code).exists()


class UserDirectoryRepository:
    def __init__(self, auth_repository: AuthenticationRepository | None = None) -> None:
        self.user_model = get_user_model()
        self.auth_repository = auth_repository or AuthenticationRepository()

    def get_all(self, query_params: dict[str, Any] | None = None):
        params = query_params or {}
        queryset = self.user_model.objects.all().prefetch_related(
            Prefetch("identity_user_roles", queryset=UserRole.objects.select_related("role"))
        )

        status = (params.get("status") or "").strip().upper()
        if status == "ACTIVE":
            queryset = queryset.filter(is_active=True)
        elif status == "INACTIVE":
            queryset = queryset.filter(is_active=False)

        role = (params.get("role") or "").strip()
        if role:
            queryset = queryset.filter(identity_user_roles__role__name__icontains=role).distinct()

        search = (params.get("search") or "").strip()
        if search:
            queryset = queryset.filter(
                Q(username__icontains=search)
                | Q(first_name__icontains=search)
                | Q(last_name__icontains=search)
                | Q(email__icontains=search)
                | Q(identity_user_roles__role__name__icontains=search)
            ).distinct()

        return queryset

    def get_roles(self, user) -> list[str]:
        return list(
            UserRole.objects.filter(user=user)
            .select_related("role")
            .values_list("role__name", flat=True)
        )

    def get_permissions(self, user) -> list[dict[str, str]]:
        access_context = self.auth_repository.get_access_context(user)
        permissions = access_context.get("permissions") or []
        normalized: list[dict[str, str]] = []
        for item in permissions:
            module = str(item.get("module", "")).strip()
            action = str(item.get("action", "")).strip()
            if not module or not action:
                continue
            normalized.append({"module": module, "action": action})
        return normalized


class AuthenticationRepository:
    def __init__(self) -> None:
        self.user_model = get_user_model()

    @staticmethod
    def _resolve_user_id(user_or_id: Any) -> Any:
        if hasattr(user_or_id, "id"):
            return getattr(user_or_id, "id")
        return user_or_id

    @staticmethod
    def _access_context_cache_key(user_id: Any) -> str:
        return f"identity:access-context:{user_id}"

    @staticmethod
    def _normalize_name(value: str) -> str:
        return (value or "").strip()

    @staticmethod
    def _split_employee_name(employee_name: str) -> tuple[str, str]:
        normalized = (employee_name or "").strip()
        if not normalized:
            return "", ""
        parts = normalized.split(" ", 1)
        if len(parts) == 1:
            return parts[0], ""
        return parts[0], parts[1]

    @staticmethod
    def _role_code(role_name: str) -> str:
        slug = slugify(role_name)[:75] or "role"
        return f"ROLE-{slug.upper()}"

    @staticmethod
    def _permission_code(module: str, action: str) -> str:
        module_slug = slugify(module)[:35] or "module"
        action_slug = slugify(action)[:35] or "action"
        return f"PERM-{module_slug.upper()}-{action_slug.upper()}"

    def get_by_username(self, username: str):
        return self.user_model.objects.filter(username=username).first()

    @transaction.atomic
    def upsert_user_from_bauthone(
        self,
        *,
        username: str,
        employee_details: dict[str, Any],
        is_staff: bool,
        is_superuser: bool,
    ):
        employee_name = (
            employee_details.get("Employee_Name_Regular")
            or employee_details.get("employeeName")
            or employee_details.get("name")
            or ""
        )
        first_name, last_name = self._split_employee_name(employee_name)
        email = (
            employee_details.get("Employee_Email")
            or employee_details.get("email")
            or employee_details.get("mail")
            or ""
        )

        user, _ = self.user_model.objects.get_or_create(username=username)
        user.first_name = self._normalize_name(first_name)
        user.last_name = self._normalize_name(last_name)
        user.email = self._normalize_name(email)
        user.is_active = True
        user.is_staff = bool(is_staff)
        user.is_superuser = bool(is_superuser)
        if user.has_usable_password():
            user.set_unusable_password()
        user.save(
            update_fields=[
                "first_name",
                "last_name",
                "email",
                "is_active",
                "is_staff",
                "is_superuser",
                "password",
            ]
        )
        return user

    @transaction.atomic
    def update_user_profile(self, user, profile_data: dict[str, Any]):
        for field in ("first_name", "last_name", "email"):
            if field in profile_data:
                setattr(user, field, self._normalize_name(profile_data.get(field, "")))
        user.save(update_fields=["first_name", "last_name", "email"])
        return user

    @transaction.atomic
    def update_password(self, user, new_password: str):
        user.set_password(new_password)
        user.save(update_fields=["password"])
        return user

    def sync_permissions(self, permission_entries: Iterable[dict[str, str]]) -> list[dict[str, str]]:
        synchronized: list[dict[str, str]] = []

        for entry in permission_entries:
            module = (entry.get("module") or "").strip()
            action = (entry.get("action") or "").strip()
            description = (entry.get("description") or "").strip()
            if not module or not action:
                continue

            permission = Permission.all_objects.filter(module=module, action=action).first()
            if permission:
                permission.description = description
                permission.status = StatusChoices.ACTIVE
                if permission.is_deleted:
                    permission.is_deleted = False
                    permission.deleted_at = None
                permission.save(update_fields=["description", "status", "is_deleted", "deleted_at"])
            else:
                permission = Permission.objects.create(
                    code=self._permission_code(module, action),
                    module=module,
                    action=action,
                    description=description,
                    status=StatusChoices.ACTIVE,
                )

            synchronized.append(
                {
                    "module": permission.module,
                    "action": permission.action,
                    "description": permission.description,
                }
            )

        return synchronized

    @transaction.atomic
    def sync_user_roles(self, user, roles: Iterable[str]) -> list[str]:
        normalized_roles = sorted({(role or "").strip() for role in roles if (role or "").strip()})

        role_objects: list[Role] = []
        for role_name in normalized_roles:
            role = Role.all_objects.filter(name=role_name).first()
            if role:
                role.status = StatusChoices.ACTIVE
                if role.is_deleted:
                    role.is_deleted = False
                    role.deleted_at = None
                role.save(update_fields=["status", "is_deleted", "deleted_at"])
            else:
                role = Role.objects.create(
                    code=self._role_code(role_name),
                    name=role_name,
                    description=f"Synced from BAUTHONE: {role_name}",
                    status=StatusChoices.ACTIVE,
                )
            role_objects.append(role)

        UserRole.all_objects.filter(user=user).delete()
        for role in role_objects:
            UserRole.objects.create(
                code=_generate_code("USRROLE"),
                user=user,
                role=role,
                status=StatusChoices.ACTIVE,
            )

        return [role.name for role in role_objects]

    def get_roles(self, user) -> list[str]:
        return list(
            UserRole.objects.filter(user=user)
            .select_related("role")
            .values_list("role__name", flat=True)
        )

    def set_access_context(self, user, context: dict[str, Any]) -> None:
        user_id = self._resolve_user_id(user)
        if not user_id:
            return
        refresh_lifetime = settings.SIMPLE_JWT.get("REFRESH_TOKEN_LIFETIME")
        timeout_seconds = int(refresh_lifetime.total_seconds()) if refresh_lifetime else 86400
        cache.set(self._access_context_cache_key(user_id), context, timeout=timeout_seconds)

    def get_access_context(self, user) -> dict[str, Any]:
        user_id = self._resolve_user_id(user)
        if not user_id:
            return {}
        return cache.get(self._access_context_cache_key(user_id), {}) or {}

    def clear_access_context(self, user) -> None:
        user_id = self._resolve_user_id(user)
        if not user_id:
            return
        cache.delete(self._access_context_cache_key(user_id))


class PermissionRepository:
    def __init__(self, auth_repository: AuthenticationRepository | None = None) -> None:
        self.auth_repository = auth_repository or AuthenticationRepository()

    def _get_permission_pairs(self, user) -> set[tuple[str, str]]:
        access_context = self.auth_repository.get_access_context(user)
        permissions = access_context.get("permissions") or []
        return {
            (
                str(item.get("module", "")).strip().lower(),
                str(item.get("action", "")).strip().lower(),
            )
            for item in permissions
            if item.get("module") and item.get("action")
        }

    def has_role(self, user, role_name: str) -> bool:
        if not user or not user.is_authenticated:
            return False
        return UserRole.objects.filter(user=user, role__name__iexact=(role_name or "").strip()).exists()

    def has_permission(self, user, module: str, action: str) -> bool:
        if not user or not user.is_authenticated:
            return False
        if user.is_superuser:
            return True

        key = ((module or "").strip().lower(), (action or "").strip().lower())
        return key in self._get_permission_pairs(user)

    def has_program_access(
        self,
        user,
        program_code: str,
        *,
        module_name: str | None = None,
        application_name: str | None = None,
    ) -> bool:
        if not user or not user.is_authenticated:
            return False
        if user.is_superuser:
            return True

        access_context = self.auth_repository.get_access_context(user)
        application = access_context.get("application") or {}
        if application_name and str(application.get("name", "")).lower() != application_name.lower():
            return False

        target_program = (program_code or "").strip().lower()
        target_module = (module_name or "").strip().lower()
        programs = access_context.get("programs") or []

        for item in programs:
            code = str(item.get("program_code", "")).strip().lower()
            module = str(item.get("module", "")).strip().lower()
            if code != target_program:
                continue
            if target_module and module != target_module:
                continue
            return True

        return False

    def has_operation(
        self,
        user,
        *,
        program_code: str,
        operation_name: str,
        module_name: str | None = None,
        application_name: str | None = None,
    ) -> bool:
        if not user or not user.is_authenticated:
            return False
        if user.is_superuser:
            return True

        access_context = self.auth_repository.get_access_context(user)
        application = access_context.get("application") or {}
        if application_name and str(application.get("name", "")).lower() != application_name.lower():
            return False

        target_program = (program_code or "").strip().lower()
        target_module = (module_name or "").strip().lower()
        target_operation = (operation_name or "").strip().lower()
        programs = access_context.get("programs") or []

        for item in programs:
            code = str(item.get("program_code", "")).strip().lower()
            module = str(item.get("module", "")).strip().lower()
            if code != target_program:
                continue
            if target_module and module != target_module:
                continue

            operations = {
                str(operation).strip().lower()
                for operation in item.get("operations") or []
                if str(operation).strip()
            }
            if target_operation in operations:
                return True

        return False


class AuthenticationAuditRepository:
    def log_activity(
        self,
        *,
        user,
        activity: str,
        description: str,
        request_id: str,
        reference_number: str = "",
    ) -> None:
        """Stub for activity logging - removed governance dependency"""
        pass

    def log_audit(
        self,
        *,
        user,
        action: str,
        entity_id: str,
        description: str,
        ip_address: str = "",
        user_agent: str = "",
    ) -> None:
        """Stub for audit logging - removed governance dependency"""
        pass