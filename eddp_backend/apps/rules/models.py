from django.db import models

from apps.common.choices import RuleTypeChoices
from apps.common.models import BaseModel


class RuleGroup(BaseModel):
	name = models.CharField(max_length=150, db_index=True)
	description = models.TextField(blank=True)
	priority = models.PositiveSmallIntegerField(default=100, db_index=True)

	class Meta:
		verbose_name = "Rule Group"
		verbose_name_plural = "Rule Groups"

	def __str__(self):
		return self.name


class Rule(BaseModel):
	rule_group = models.ForeignKey(
		RuleGroup,
		on_delete=models.PROTECT,
		related_name="rules",
	)
	name = models.CharField(max_length=150, db_index=True)
	description = models.TextField(blank=True)
	# TODO:
	# Add pluggable support for Python/JSONLogic expression engines.
	expression = models.TextField()
	rule_type = models.CharField(
		max_length=100,
		choices=RuleTypeChoices.choices,
		db_index=True,
	)
	execution_order = models.PositiveIntegerField(default=1, db_index=True)
	is_active = models.BooleanField(default=True, db_index=True)

	class Meta:
		verbose_name = "Rule"
		verbose_name_plural = "Rules"
		ordering = ["execution_order"]
		constraints = [
			models.UniqueConstraint(
				fields=["rule_group", "name"],
				name="uq_rule_group_rule_name",
			)
		]

	def __str__(self):
		return self.name
