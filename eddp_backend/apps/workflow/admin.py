from django.contrib import admin

from .models import Workflow, WorkflowHistory, WorkflowStep


BASE_READONLY_FIELDS = (
	"id",
	"created_at",
	"updated_at",
	"deleted_at",
	"created_by",
	"updated_by",
)


@admin.register(Workflow)
class WorkflowAdmin(admin.ModelAdmin):
	list_display = (
		"code",
		"name",
		"workflow_type",
		"applicable_document",
		"version",
		"is_default",
		"status",
		"is_deleted",
		"created_at",
	)
	search_fields = (
		"code",
		"name",
		"description",
		"workflow_type",
		"applicable_document__name",
		"applicable_document__code",
	)
	list_filter = (
		"status",
		"is_deleted",
		"workflow_type",
		"is_default",
		"applicable_document",
		"created_at",
	)
	readonly_fields = BASE_READONLY_FIELDS
	ordering = ("-created_at",)
	date_hierarchy = "created_at"
	list_per_page = 25
	autocomplete_fields = ("applicable_document",)
	list_select_related = ("applicable_document",)


@admin.register(WorkflowStep)
class WorkflowStepAdmin(admin.ModelAdmin):
	list_display = (
		"code",
		"workflow",
		"step_name",
		"step_order",
		"approver_role",
		"action_type",
		"is_mandatory",
		"status",
		"is_deleted",
		"created_at",
	)
	search_fields = (
		"code",
		"step_name",
		"workflow__name",
		"workflow__code",
		"approver_role__name",
		"approver_role__code",
	)
	list_filter = (
		"status",
		"is_deleted",
		"action_type",
		"is_mandatory",
		"workflow",
		"approver_role",
		"created_at",
	)
	readonly_fields = BASE_READONLY_FIELDS
	ordering = ("workflow", "step_order", "-created_at")
	date_hierarchy = "created_at"
	list_per_page = 25
	autocomplete_fields = ("workflow", "approver_role")
	list_select_related = ("workflow", "approver_role")


@admin.register(WorkflowHistory)
class WorkflowHistoryAdmin(admin.ModelAdmin):
	list_display = (
		"code",
		"workflow",
		"document_reference",
		"current_step",
		"performed_by",
		"action",
		"performed_at",
		"status",
		"is_deleted",
	)
	search_fields = (
		"code",
		"document_reference",
		"remarks",
		"workflow__name",
		"workflow__code",
		"performed_by__username",
		"performed_by__email",
	)
	list_filter = ("status", "is_deleted", "action", "performed_at", "created_at")
	readonly_fields = BASE_READONLY_FIELDS + ("performed_at",)
	ordering = ("-performed_at", "-created_at")
	date_hierarchy = "performed_at"
	list_per_page = 25
	autocomplete_fields = ("workflow", "current_step", "performed_by")
	list_select_related = ("workflow", "current_step", "performed_by")
