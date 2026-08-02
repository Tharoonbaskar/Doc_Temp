from django.contrib import admin

from .models import Variable, VariableCategory, VariableGroup


BASE_READONLY_FIELDS = (
	"id",
	"created_at",
	"updated_at",
	"deleted_at",
	"created_by",
	"updated_by",
)


@admin.register(VariableCategory)
class VariableCategoryAdmin(admin.ModelAdmin):
	list_display = ("code", "name", "status", "is_deleted", "created_at", "updated_at")
	search_fields = ("code", "name", "description")
	list_filter = ("status", "is_deleted", "created_at", "updated_at")
	readonly_fields = BASE_READONLY_FIELDS
	ordering = ("-created_at",)
	date_hierarchy = "created_at"
	list_per_page = 25


@admin.register(VariableGroup)
class VariableGroupAdmin(admin.ModelAdmin):
	list_display = ("code", "name", "category", "status", "is_deleted", "created_at")
	search_fields = ("code", "name", "description", "category__name", "category__code")
	list_filter = ("status", "is_deleted", "category", "created_at")
	readonly_fields = BASE_READONLY_FIELDS
	ordering = ("-created_at",)
	date_hierarchy = "created_at"
	list_per_page = 25
	autocomplete_fields = ("category",)
	list_select_related = ("category",)


@admin.register(Variable)
class VariableAdmin(admin.ModelAdmin):
	list_display = (
		"code",
		"name",
		"display_name",
		"group",
		"data_type",
		"source_type",
		"is_required",
		"status",
		"is_deleted",
		"created_at",
	)
	search_fields = (
		"code",
		"name",
		"display_name",
		"description",
		"source_reference",
		"group__name",
		"group__code",
	)
	list_filter = (
		"status",
		"is_deleted",
		"data_type",
		"source_type",
		"is_required",
		"group",
		"created_at",
	)
	readonly_fields = BASE_READONLY_FIELDS
	ordering = ("-created_at",)
	date_hierarchy = "created_at"
	list_per_page = 25
	autocomplete_fields = ("group",)
	list_select_related = ("group",)
