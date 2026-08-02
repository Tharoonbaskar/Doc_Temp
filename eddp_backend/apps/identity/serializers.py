from __future__ import annotations

from django.contrib.auth.password_validation import validate_password
from django.contrib.auth import get_user_model
from rest_framework import serializers

from apps.common.serializers import BaseAuditModelSerializer, UserSummarySerializer

from .models import Permission, Role, UserRole


class RoleSerializer(BaseAuditModelSerializer):
    class Meta:
        model = Role
        fields = (
            "id",
            "code",
            "name",
            "description",
            "status",
            "created_at",
            "updated_at",
            "created_by",
            "updated_by",
            "is_deleted",
            "deleted_at",
        )
        read_only_fields = BaseAuditModelSerializer.AUDIT_READONLY_FIELDS

    def validate_name(self, value: str) -> str:
        return self.ensure_non_empty(value, "name")


class PermissionSerializer(BaseAuditModelSerializer):
    class Meta:
        model = Permission
        fields = (
            "id",
            "code",
            "module",
            "action",
            "description",
            "status",
            "created_at",
            "updated_at",
            "created_by",
            "updated_by",
            "is_deleted",
            "deleted_at",
        )
        read_only_fields = BaseAuditModelSerializer.AUDIT_READONLY_FIELDS

    def validate_module(self, value: str) -> str:
        return self.ensure_non_empty(value, "module")

    def validate_action(self, value: str) -> str:
        return self.ensure_non_empty(value, "action")


class UserRoleSerializer(BaseAuditModelSerializer):
    user = UserSummarySerializer(read_only=True)
    user_id = serializers.PrimaryKeyRelatedField(
        source="user",
        queryset=get_user_model().objects.all(),
        write_only=True,
    )
    role = RoleSerializer(read_only=True)
    role_id = serializers.PrimaryKeyRelatedField(
        source="role",
        queryset=Role.objects.all(),
        write_only=True,
    )

    class Meta:
        model = UserRole
        fields = (
            "id",
            "code",
            "user",
            "user_id",
            "role",
            "role_id",
            "status",
            "created_at",
            "updated_at",
            "created_by",
            "updated_by",
            "is_deleted",
            "deleted_at",
        )
        read_only_fields = BaseAuditModelSerializer.AUDIT_READONLY_FIELDS

    def validate(self, attrs):
        attrs = super().validate(attrs)
        user = attrs.get("user") or getattr(self.instance, "user", None)
        role = attrs.get("role") or getattr(self.instance, "role", None)

        if not user:
            raise serializers.ValidationError({"user_id": "This field is required."})
        if not role:
            raise serializers.ValidationError({"role_id": "This field is required."})

        queryset = UserRole.all_objects.filter(user=user, role=role)
        if self.instance is not None:
            queryset = queryset.exclude(pk=self.instance.pk)
        if queryset.exists():
            raise serializers.ValidationError("This user-role mapping already exists.")

        return attrs


class AuthLoginSerializer(serializers.Serializer):
    username = serializers.CharField(required=False, allow_blank=True)
    password = serializers.CharField(required=False, allow_blank=True, write_only=True, trim_whitespace=False)
    userName = serializers.CharField(required=False, allow_blank=True, write_only=True)
    passWord = serializers.CharField(required=False, allow_blank=True, write_only=True, trim_whitespace=False)

    def validate(self, attrs):
        username = (attrs.get("username") or attrs.get("userName") or "").strip()
        password = attrs.get("password") or attrs.get("passWord") or ""
        if not username:
            raise serializers.ValidationError({"username": "Username is required."})
        if not password:
            raise serializers.ValidationError({"password": "Password is required."})
        return {"username": username, "password": password}


class AuthLogoutSerializer(serializers.Serializer):
    refresh = serializers.CharField(required=True)


class AuthRefreshSerializer(serializers.Serializer):
    refresh = serializers.CharField(required=True)


class AuthVerifySerializer(serializers.Serializer):
    token = serializers.CharField(required=True)


class ProfileUpdateSerializer(serializers.Serializer):
    first_name = serializers.CharField(required=False, allow_blank=True, max_length=150)
    last_name = serializers.CharField(required=False, allow_blank=True, max_length=150)
    email = serializers.EmailField(required=False, allow_blank=True)


class ChangePasswordSerializer(serializers.Serializer):
    current_password = serializers.CharField(required=True, write_only=True, trim_whitespace=False)
    new_password = serializers.CharField(required=True, write_only=True, trim_whitespace=False)
    confirm_password = serializers.CharField(required=True, write_only=True, trim_whitespace=False)

    def validate(self, attrs):
        new_password = attrs.get("new_password", "")
        confirm_password = attrs.get("confirm_password", "")
        if new_password != confirm_password:
            raise serializers.ValidationError({"confirm_password": "Password confirmation does not match."})

        request = self.context.get("request")
        user = getattr(request, "user", None) if request else None
        validate_password(new_password, user=user)
        return attrs
