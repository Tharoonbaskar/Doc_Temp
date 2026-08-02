from django.contrib import admin

from .models import Rule, RuleGroup


BASE_READONLY_FIELDS = (
	"id",
	"created_at",
	"updated_at",
	"deleted_at",
	"created_by",
	"updated_by",
)


@admin.register(RuleGroup)
class RuleGroupAdmin(admin.ModelAdmin):
	list_display = (
		"code",
		"name",
		"priority",
		"status",
		"is_deleted",
		"created_at",
		"updated_at",
	)
	search_fields = ("code", "name", "description")
	list_filter = ("status", "is_deleted", "priority", "created_at")
	readonly_fields = BASE_READONLY_FIELDS
	ordering = ("priority", "-created_at")
	date_hierarchy = "created_at"
	list_per_page = 25


@admin.register(Rule)
class RuleAdmin(admin.ModelAdmin):
	list_display = (
		"code",
		"name",
		"rule_group",
		"rule_type",
		"execution_order",
		"is_active",
		"status",
		"is_deleted",
		"created_at",
	)
	search_fields = (
		"code",
		"name",
		"description",
		"expression",
		"rule_group__name",
		"rule_group__code",
	)
	list_filter = (
		"status",
		"is_deleted",
		"rule_type",
		"is_active",
		"rule_group",
		"created_at",
	)
	readonly_fields = BASE_READONLY_FIELDS
	ordering = ("rule_group", "execution_order", "-created_at")
	date_hierarchy = "created_at"
	list_per_page = 25
	autocomplete_fields = ("rule_group",)
	list_select_related = ("rule_group",)
