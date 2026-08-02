from django.conf import settings
from django.db import models

from apps.common.models import BaseModel


# TODO:
# Integrate audit/activity events with centralized SIEM and log aggregation
# pipelines (e.g., Azure Monitor, ELK, Splunk, Datadog).
class AuditLog(BaseModel):
	entity_name = models.CharField(max_length=150, db_index=True)
	entity_id = models.CharField(max_length=100, db_index=True)
	action = models.CharField(max_length=100, db_index=True)
	old_value = models.JSONField(default=dict, blank=True)
	new_value = models.JSONField(default=dict, blank=True)
	performed_by = models.ForeignKey(
		settings.AUTH_USER_MODEL,
		on_delete=models.SET_NULL,
		null=True,
		blank=True,
		related_name="governance_audit_logs",
	)
	ip_address = models.GenericIPAddressField(null=True, blank=True, db_index=True)
	user_agent = models.CharField(max_length=512, blank=True)
	created_on = models.DateTimeField(auto_now_add=True, db_index=True)

	class Meta:
		verbose_name = "Audit Log"
		verbose_name_plural = "Audit Logs"

	def __str__(self):
		return f"{self.entity_name}:{self.entity_id} - {self.action}"


class ActivityLog(BaseModel):
	module = models.CharField(max_length=100, db_index=True)
	activity = models.CharField(max_length=150, db_index=True)
	reference_number = models.CharField(max_length=255, blank=True, db_index=True)
	description = models.TextField(blank=True)
	performed_by = models.ForeignKey(
		settings.AUTH_USER_MODEL,
		on_delete=models.SET_NULL,
		null=True,
		blank=True,
		related_name="governance_activity_logs",
	)
	activity_time = models.DateTimeField(auto_now_add=True, db_index=True)

	class Meta:
		verbose_name = "Activity Log"
		verbose_name_plural = "Activity Logs"

	def __str__(self):
		return f"{self.module} - {self.activity}"
