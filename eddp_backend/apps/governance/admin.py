from django.contrib import admin

from .models import ActivityLog, AuditLog


BASE_READONLY_FIELDS = (
	"id",
	"created_at",
	"updated_at",
	"deleted_at",
	"created_by",
	"updated_by",
)


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
	list_display = (
		"code",
		"entity_name",
		"entity_id",
		"action",
		"performed_by",
		"ip_address",
		"created_on",
		"status",
		"is_deleted",
	)
	search_fields = (
		"code",
		"entity_name",
		"entity_id",
		"action",
		"ip_address",
		"user_agent",
		"performed_by__username",
		"performed_by__email",
	)
	list_filter = ("status", "is_deleted", "action", "entity_name", "created_on", "created_at")
	readonly_fields = BASE_READONLY_FIELDS + ("created_on",)
	ordering = ("-created_on", "-created_at")
	date_hierarchy = "created_on"
	list_per_page = 25
	autocomplete_fields = ("performed_by",)
	list_select_related = ("performed_by",)


@admin.register(ActivityLog)
class ActivityLogAdmin(admin.ModelAdmin):
	list_display = (
		"code",
		"module",
		"activity",
		"reference_number",
		"performed_by",
		"activity_time",
		"status",
		"is_deleted",
	)
	search_fields = (
		"code",
		"module",
		"activity",
		"reference_number",
		"description",
		"performed_by__username",
		"performed_by__email",
	)
	list_filter = ("status", "is_deleted", "module", "activity_time", "created_at")
	readonly_fields = BASE_READONLY_FIELDS + ("activity_time",)
	ordering = ("-activity_time", "-created_at")
	date_hierarchy = "activity_time"
	list_per_page = 25
	autocomplete_fields = ("performed_by",)
	list_select_related = ("performed_by",)
