from django.contrib import admin

from .models import GeneratedDocument, GenerationRequest, RuntimeContext


BASE_READONLY_FIELDS = (
	"id",
	"created_at",
	"updated_at",
	"deleted_at",
	"created_by",
	"updated_by",
)


@admin.register(GenerationRequest)
class GenerationRequestAdmin(admin.ModelAdmin):
	list_display = (
		"request_id",
		"code",
		"document",
		"template_version",
		"request_source",
		"business_reference",
		"requested_by",
		"requested_at",
		"completed_at",
		"status",
	)
	search_fields = (
		"request_id",
		"code",
		"business_reference",
		"request_source",
		"document__name",
		"document__code",
		"template_version__version_name",
		"template_version__code",
	)
	list_filter = (
		"status",
		"is_deleted",
		"request_source",
		"requested_at",
		"completed_at",
		"created_at",
	)
	readonly_fields = BASE_READONLY_FIELDS + ("request_id", "requested_at", "completed_at")
	ordering = ("-requested_at", "-created_at")
	date_hierarchy = "requested_at"
	list_per_page = 25
	autocomplete_fields = ("document", "template_version", "requested_by")
	list_select_related = ("document", "template_version", "requested_by")


@admin.register(RuntimeContext)
class RuntimeContextAdmin(admin.ModelAdmin):
	list_display = (
		"code",
		"generation_request",
		"status",
		"is_deleted",
		"created_at",
		"updated_at",
	)
	search_fields = (
		"code",
		"generation_request__code",
		"generation_request__request_id",
		"generation_request__business_reference",
	)
	list_filter = ("status", "is_deleted", "created_at", "updated_at")
	readonly_fields = BASE_READONLY_FIELDS
	ordering = ("-created_at",)
	date_hierarchy = "created_at"
	list_per_page = 25
	autocomplete_fields = ("generation_request",)
	list_select_related = ("generation_request",)


@admin.register(GeneratedDocument)
class GeneratedDocumentAdmin(admin.ModelAdmin):
	list_display = (
		"code",
		"generation_request",
		"file_name",
		"file_type",
		"file_size",
		"generated_at",
		"expiry_date",
		"status",
		"is_deleted",
	)
	search_fields = (
		"code",
		"file_name",
		"file_path",
		"checksum",
		"generation_request__code",
		"generation_request__request_id",
	)
	list_filter = (
		"status",
		"is_deleted",
		"file_type",
		"generated_at",
		"expiry_date",
		"created_at",
	)
	readonly_fields = BASE_READONLY_FIELDS + ("generated_at",)
	ordering = ("-generated_at", "-created_at")
	date_hierarchy = "generated_at"
	list_per_page = 25
	autocomplete_fields = ("generation_request",)
	list_select_related = ("generation_request",)
