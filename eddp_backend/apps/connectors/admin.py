from django.contrib import admin

from .models import Connector, ConnectorConfiguration


BASE_READONLY_FIELDS = (
	"id",
	"created_at",
	"updated_at",
	"deleted_at",
	"created_by",
	"updated_by",
)


@admin.register(Connector)
class ConnectorAdmin(admin.ModelAdmin):
	list_display = (
		"code",
		"name",
		"connector_type",
		"host",
		"port",
		"database_name",
		"is_active",
		"status",
		"is_deleted",
		"created_at",
	)
	search_fields = (
		"code",
		"name",
		"description",
		"host",
		"database_name",
		"username",
		"api_base_url",
	)
	list_filter = (
		"status",
		"is_deleted",
		"is_active",
		"connector_type",
		"created_at",
	)
	readonly_fields = BASE_READONLY_FIELDS
	ordering = ("-created_at",)
	date_hierarchy = "created_at"
	list_per_page = 25


@admin.register(ConnectorConfiguration)
class ConnectorConfigurationAdmin(admin.ModelAdmin):
	list_display = (
		"code",
		"connector",
		"authentication_type",
		"status",
		"is_deleted",
		"created_at",
	)
	search_fields = (
		"code",
		"connector__name",
		"connector__code",
		"authentication_type",
	)
	list_filter = ("status", "is_deleted", "authentication_type", "created_at")
	readonly_fields = BASE_READONLY_FIELDS
	ordering = ("-created_at",)
	date_hierarchy = "created_at"
	list_per_page = 25
	autocomplete_fields = ("connector",)
	list_select_related = ("connector",)
