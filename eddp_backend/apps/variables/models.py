from django.db import models

from apps.common.choices import DataTypeChoices, SourceTypeChoices
from apps.common.models import BaseModel


class VariableCategory(BaseModel):
	name = models.CharField(max_length=150, unique=True, db_index=True)
	description = models.TextField(blank=True)

	class Meta:
		verbose_name = "Variable Category"
		verbose_name_plural = "Variable Categories"

	def __str__(self):
		return self.name


class VariableGroup(BaseModel):
	name = models.CharField(max_length=150, db_index=True)
	description = models.TextField(blank=True)
	category = models.ForeignKey(
		VariableCategory,
		on_delete=models.PROTECT,
		related_name="variable_groups",
	)

	class Meta:
		verbose_name = "Variable Group"
		verbose_name_plural = "Variable Groups"
		constraints = [
			models.UniqueConstraint(
				fields=["category", "name"],
				name="uq_variable_group_category_name",
			)
		]

	def __str__(self):
		return self.name


class Variable(BaseModel):
	group = models.ForeignKey(
		VariableGroup,
		on_delete=models.CASCADE,
		related_name="variables",
	)
	name = models.CharField(max_length=150, db_index=True)
	display_name = models.CharField(max_length=255, db_index=True)
	description = models.TextField(blank=True)
	data_type = models.CharField(
		max_length=50,
		choices=DataTypeChoices.choices,
		db_index=True,
	)
	source_type = models.CharField(
		max_length=50,
		choices=SourceTypeChoices.choices,
		db_index=True,
	)
	# TODO:
	# Replace with ForeignKey to Connector/Data Mapping module
	# after implementation.
	source_reference = models.CharField(max_length=255, blank=True, db_index=True)
	default_value = models.TextField(blank=True)
	is_required = models.BooleanField(default=False, db_index=True)
	# Many-to-many relationship with documents
	documents = models.ManyToManyField(
		"documents.Document",
		related_name="variables",
		blank=True,
	)

	class Meta:
		verbose_name = "Variable"
		verbose_name_plural = "Variables"
		constraints = [
			models.UniqueConstraint(
				fields=["group", "name"],
				name="uq_variable_group_name",
			)
		]

	def __str__(self):
		return self.display_name
