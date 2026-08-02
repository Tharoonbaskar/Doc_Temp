from django.db import models

from apps.common.choices import AuthenticationTypeChoices, ConnectorTypeChoices
from apps.common.models import BaseModel


class Connector(BaseModel):
	name = models.CharField(max_length=150, unique=True, db_index=True)
	connector_type = models.CharField(
		max_length=100,
		choices=ConnectorTypeChoices.choices,
		db_index=True,
	)
	description = models.TextField(blank=True)
	host = models.CharField(max_length=255, blank=True, db_index=True)
	port = models.PositiveIntegerField(null=True, blank=True, db_index=True)
	database_name = models.CharField(max_length=150, blank=True, db_index=True)
	username = models.CharField(max_length=150, blank=True)
	# TODO:
	# Store password using field-level encryption or integrate with
	# HashiCorp Vault / Azure Key Vault / AWS Secrets Manager.
	password = models.CharField(max_length=255, blank=True)
	api_base_url = models.URLField(max_length=500, blank=True)
	timeout = models.PositiveIntegerField(default=30)
	retry_count = models.PositiveSmallIntegerField(default=3)
	is_active = models.BooleanField(default=True, db_index=True)

	class Meta:
		verbose_name = "Connector"
		verbose_name_plural = "Connectors"

	def __str__(self):
		return self.name


class ConnectorConfiguration(BaseModel):
	connector = models.OneToOneField(
		Connector,
		on_delete=models.CASCADE,
		related_name="configuration",
	)
	configuration_json = models.JSONField(default=dict, blank=True)
	headers_json = models.JSONField(default=dict, blank=True)
	authentication_type = models.CharField(
		max_length=50,
		choices=AuthenticationTypeChoices.choices,
		db_index=True,
	)
	authentication_json = models.JSONField(default=dict, blank=True)

	class Meta:
		verbose_name = "Connector Configuration"
		verbose_name_plural = "Connector Configurations"

	def __str__(self):
		return f"Configuration: {self.connector.name}"
