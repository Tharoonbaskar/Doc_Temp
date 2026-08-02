from django.conf import settings
from django.db import models

from apps.common.models import BaseModel


class Role(BaseModel):
	name = models.CharField(max_length=150, unique=True, db_index=True)
	description = models.TextField(blank=True)

	class Meta:
		verbose_name = "Role"
		verbose_name_plural = "Roles"

	def __str__(self):
		return self.name


class Permission(BaseModel):
	module = models.CharField(max_length=100, db_index=True)
	action = models.CharField(max_length=100, db_index=True)
	description = models.TextField(blank=True)

	class Meta:
		verbose_name = "Permission"
		verbose_name_plural = "Permissions"
		constraints = [
			models.UniqueConstraint(
				fields=["module", "action"],
				name="uq_permission_module_action",
			)
		]

	def __str__(self):
		return f"{self.module}:{self.action}"


class UserRole(BaseModel):
	user = models.ForeignKey(
		settings.AUTH_USER_MODEL,
		on_delete=models.CASCADE,
		related_name="identity_user_roles",
	)
	role = models.ForeignKey(
		Role,
		on_delete=models.CASCADE,
		related_name="user_roles",
	)

	class Meta:
		verbose_name = "User Role"
		verbose_name_plural = "User Roles"
		constraints = [
			models.UniqueConstraint(
				fields=["user", "role"],
				name="uq_user_role",
			)
		]

	def __str__(self):
		return f"{self.user} - {self.role}"
