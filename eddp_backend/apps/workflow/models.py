from django.conf import settings
from django.db import models

from apps.common.choices import WorkflowActionChoices
from apps.common.models import BaseModel
from apps.documents.models import Document
from apps.identity.models import Role


class Workflow(BaseModel):
	name = models.CharField(max_length=150, db_index=True)
	description = models.TextField(blank=True)
	workflow_type = models.CharField(max_length=100, db_index=True)
	applicable_document = models.ForeignKey(
		Document,
		on_delete=models.PROTECT,
		related_name="workflows",
	)
	version = models.PositiveIntegerField(default=1, db_index=True)
	is_default = models.BooleanField(default=False, db_index=True)

	class Meta:
		verbose_name = "Workflow"
		verbose_name_plural = "Workflows"

	def __str__(self):
		return self.name


class WorkflowStep(BaseModel):
	workflow = models.ForeignKey(
		Workflow,
		on_delete=models.CASCADE,
		related_name="steps",
	)
	step_name = models.CharField(max_length=150, db_index=True)
	step_order = models.PositiveIntegerField(db_index=True)
	approver_role = models.ForeignKey(
		Role,
		on_delete=models.PROTECT,
		related_name="workflow_steps",
	)
	action_type = models.CharField(
		max_length=100,
		choices=WorkflowActionChoices.choices,
		db_index=True,
	)
	is_mandatory = models.BooleanField(default=True, db_index=True)

	class Meta:
		verbose_name = "Workflow Step"
		verbose_name_plural = "Workflow Steps"
		ordering = ["step_order"]
		constraints = [
			models.UniqueConstraint(
				fields=["workflow", "step_order"],
				name="uq_workflow_step_order",
			)
		]

	def __str__(self):
		return f"{self.workflow.name} - {self.step_name}"


class WorkflowHistory(BaseModel):
	workflow = models.ForeignKey(
		Workflow,
		on_delete=models.CASCADE,
		related_name="history_entries",
	)
	document_reference = models.CharField(max_length=255, db_index=True)
	current_step = models.ForeignKey(
		WorkflowStep,
		on_delete=models.SET_NULL,
		null=True,
		blank=True,
		related_name="history_entries",
	)
	performed_by = models.ForeignKey(
		settings.AUTH_USER_MODEL,
		on_delete=models.SET_NULL,
		null=True,
		blank=True,
		related_name="workflow_history_entries",
	)
	action = models.CharField(
		max_length=100,
		choices=WorkflowActionChoices.choices,
		db_index=True,
	)
	remarks = models.TextField(blank=True)
	performed_at = models.DateTimeField(auto_now_add=True, db_index=True)

	class Meta:
		verbose_name = "Workflow History"
		verbose_name_plural = "Workflow Histories"

	def __str__(self):
		return f"{self.workflow.name} - {self.action}"
