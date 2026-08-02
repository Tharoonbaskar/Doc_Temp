from django.contrib import admin

from .models import Permission, Role, UserRole


BASE_READONLY_FIELDS = (
	"id",
	"created_at",
	"updated_at",
	"deleted_at",
	"created_by",
	"updated_by",
)


@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
	list_display = ("code", "name", "status", "is_deleted", "created_at", "updated_at")
	search_fields = ("code", "name", "description")
	list_filter = ("status", "is_deleted", "created_at", "updated_at")
	readonly_fields = BASE_READONLY_FIELDS
	ordering = ("-created_at",)
	date_hierarchy = "created_at"
	list_per_page = 25


@admin.register(Permission)
class PermissionAdmin(admin.ModelAdmin):
	list_display = ("code", "module", "action", "status", "is_deleted", "created_at")
	search_fields = ("code", "module", "action", "description")
	list_filter = ("status", "is_deleted", "module", "action", "created_at")
	readonly_fields = BASE_READONLY_FIELDS
	ordering = ("-created_at",)
	date_hierarchy = "created_at"
	list_per_page = 25


@admin.register(UserRole)
class UserRoleAdmin(admin.ModelAdmin):
	list_display = ("code", "user", "role", "status", "is_deleted", "created_at")
	search_fields = (
		"code",
		"user__username",
		"user__email",
		"role__name",
		"role__code",
	)
	list_filter = ("status", "is_deleted", "role", "created_at")
	readonly_fields = BASE_READONLY_FIELDS
	ordering = ("-created_at",)
	date_hierarchy = "created_at"
	list_per_page = 25
	list_select_related = ("user", "role")
