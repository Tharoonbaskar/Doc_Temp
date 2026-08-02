from django.contrib import admin

from .models import Template, TemplateComponent, TemplateStyle, TemplateVersion


BASE_READONLY_FIELDS = (
	"id",
	"created_at",
	"updated_at",
	"deleted_at",
	"created_by",
	"updated_by",
)


@admin.register(Template)
class TemplateAdmin(admin.ModelAdmin):
	list_display = (
		"code",
		"name",
		"document",
		"template_type",
		"content_type",
		"is_default",
		"status",
		"is_deleted",
		"created_at",
	)
	search_fields = (
		"code",
		"name",
		"description",
		"category",
		"template_type",
		"content_type",
		"document__name",
		"document__code",
	)
	list_filter = (
		"status",
		"is_deleted",
		"is_default",
		"template_type",
		"content_type",
		"document",
		"created_at",
	)
	readonly_fields = BASE_READONLY_FIELDS
	ordering = ("-created_at",)
	date_hierarchy = "created_at"
	list_per_page = 25
	autocomplete_fields = ("document",)
	list_select_related = ("document",)


@admin.register(TemplateVersion)
class TemplateVersionAdmin(admin.ModelAdmin):
	list_display = (
		"code",
		"template",
		"version_number",
		"version_name",
		"published_at",
		"status",
		"is_deleted",
		"created_at",
	)
	search_fields = (
		"code",
		"version_name",
		"template__name",
		"template__code",
	)
	list_filter = ("status", "is_deleted", "published_at", "created_at")
	readonly_fields = BASE_READONLY_FIELDS
	ordering = ("-created_at",)
	date_hierarchy = "created_at"
	list_per_page = 25
	autocomplete_fields = ("template",)
	list_select_related = ("template",)


@admin.register(TemplateComponent)
class TemplateComponentAdmin(admin.ModelAdmin):
	list_display = (
		"code",
		"template_version",
		"component_name",
		"component_type",
		"display_order",
		"status",
		"is_deleted",
		"created_at",
	)
	search_fields = (
		"code",
		"component_name",
		"component_type",
		"template_version__version_name",
		"template_version__code",
	)
	list_filter = ("status", "is_deleted", "component_type", "created_at")
	readonly_fields = BASE_READONLY_FIELDS
	ordering = ("template_version", "display_order", "-created_at")
	date_hierarchy = "created_at"
	list_per_page = 25
	autocomplete_fields = ("template_version",)
	list_select_related = ("template_version",)


@admin.register(TemplateStyle)
class TemplateStyleAdmin(admin.ModelAdmin):
	list_display = (
		"code",
		"template_version",
		"page_size",
		"orientation",
		"default_font",
		"default_font_size",
		"status",
		"is_deleted",
		"created_at",
	)
	search_fields = (
		"code",
		"default_font",
		"template_version__version_name",
		"template_version__code",
	)
	list_filter = (
		"status",
		"is_deleted",
		"page_size",
		"orientation",
		"created_at",
	)
	readonly_fields = BASE_READONLY_FIELDS
	ordering = ("-created_at",)
	date_hierarchy = "created_at"
	list_per_page = 25
	autocomplete_fields = ("template_version",)
	list_select_related = ("template_version",)
