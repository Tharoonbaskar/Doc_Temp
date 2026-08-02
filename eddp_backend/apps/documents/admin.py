from django.contrib import admin

from .models import Document, DocumentCategory, DocumentDefinition, DocumentPackage


BASE_READONLY_FIELDS = (
	"id",
	"created_at",
	"updated_at",
	"deleted_at",
	"created_by",
	"updated_by",
)


@admin.register(DocumentCategory)
class DocumentCategoryAdmin(admin.ModelAdmin):
	list_display = ("code", "name", "status", "is_deleted", "created_at", "updated_at")
	search_fields = ("code", "name", "description")
	list_filter = ("status", "is_deleted", "created_at", "updated_at")
	readonly_fields = BASE_READONLY_FIELDS
	ordering = ("-created_at",)
	date_hierarchy = "created_at"
	list_per_page = 25


@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
	list_display = (
		"code",
		"name",
		"category",
		"document_type",
		"business_module",
		"product",
		"output_format",
		"status",
		"is_deleted",
		"created_at",
	)
	search_fields = (
		"code",
		"name",
		"description",
		"document_type",
		"business_module",
		"product",
		"output_format",
		"category__name",
		"category__code",
	)
	list_filter = (
		"status",
		"is_deleted",
		"category",
		"document_type",
		"business_module",
		"product",
		"output_format",
		"created_at",
	)
	readonly_fields = BASE_READONLY_FIELDS
	ordering = ("-created_at",)
	date_hierarchy = "created_at"
	autocomplete_fields = ("category",)
	list_select_related = ("category",)
	list_per_page = 25


@admin.register(DocumentDefinition)
class DocumentDefinitionAdmin(admin.ModelAdmin):
	list_display = (
		"code",
		"document",
		"active_template_code",
		"variable_group_code",
		"connector_code",
		"rule_group_code",
		"language",
		"effective_from",
		"effective_to",
		"status",
		"is_deleted",
	)
	search_fields = (
		"code",
		"document__name",
		"document__code",
		"active_template_code",
		"variable_group_code",
		"connector_code",
		"rule_group_code",
	)
	list_filter = (
		"status",
		"is_deleted",
		"language",
		"effective_from",
		"effective_to",
		"created_at",
	)
	readonly_fields = BASE_READONLY_FIELDS
	ordering = ("-created_at",)
	date_hierarchy = "created_at"
	autocomplete_fields = ("document",)
	list_select_related = ("document",)
	list_per_page = 25


@admin.register(DocumentPackage)
class DocumentPackageAdmin(admin.ModelAdmin):
	list_display = (
		"code",
		"name",
		"status",
		"is_deleted",
		"created_at",
		"updated_at",
		"document_count",
	)
	search_fields = ("code", "name", "description", "documents__name", "documents__code")
	list_filter = ("status", "is_deleted", "created_at", "updated_at")
	readonly_fields = BASE_READONLY_FIELDS
	ordering = ("-created_at",)
	date_hierarchy = "created_at"
	filter_horizontal = ("documents",)
	list_per_page = 25

	@admin.display(description="Documents")
	def document_count(self, obj):
		return obj.documents.count()
