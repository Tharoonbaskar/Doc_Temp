from django.db import models

from apps.common.choices import DocumentTypeChoices, LanguageChoices, OutputFormatChoices
from apps.common.models import BaseModel


class DocumentCategory(BaseModel):
	name = models.CharField(
		max_length=150,
		unique=True,
		db_index=True,
	)
	description = models.TextField(blank=True)

	class Meta:
		verbose_name = "Document Category"
		verbose_name_plural = "Document Categories"

	def __str__(self):
		return self.name


class Document(BaseModel):
	category = models.ForeignKey(
		DocumentCategory,
		on_delete=models.PROTECT,
		related_name="documents",
	)
	name = models.CharField(max_length=255, db_index=True)
	document_type = models.CharField(
		max_length=100,
		choices=DocumentTypeChoices.choices,
		db_index=True,
	)
	business_module = models.CharField(max_length=100, db_index=True)
	product = models.CharField(max_length=100, db_index=True)
	output_format = models.CharField(
		max_length=50,
		choices=OutputFormatChoices.choices,
		db_index=True,
	)
	description = models.TextField(blank=True)

	class Meta:
		verbose_name = "Document"
		verbose_name_plural = "Documents"
		constraints = [
			models.UniqueConstraint(
				fields=["category", "name"],
				name="uq_document_category_name",
			)
		]

	def __str__(self):
		return self.name


class DocumentDefinition(BaseModel):
	document = models.OneToOneField(
		Document,
		on_delete=models.CASCADE,
		related_name="definition",
	)
	# TODO:
	# Replace with ForeignKey after Template,
	# Variable, Connector and Rule modules are implemented.
	active_template_code = models.CharField(max_length=100, db_index=True)
	variable_group_code = models.CharField(max_length=100, db_index=True)
	connector_code = models.CharField(max_length=100, db_index=True)
	rule_group_code = models.CharField(max_length=100, db_index=True)
	language = models.CharField(
		max_length=2,
		choices=LanguageChoices.choices,
		db_index=True,
	)
	effective_from = models.DateTimeField(db_index=True)
	effective_to = models.DateTimeField(null=True, blank=True, db_index=True)

	class Meta:
		verbose_name = "Document Definition"
		verbose_name_plural = "Document Definitions"

	def __str__(self):
		return f"Definition: {self.document.name}"


class DocumentPackage(BaseModel):
	name = models.CharField(max_length=255, db_index=True)
	description = models.TextField(blank=True)
	documents = models.ManyToManyField(
		Document,
		related_name="packages",
		blank=True,
	)

	class Meta:
		verbose_name = "Document Package"
		verbose_name_plural = "Document Packages"

	def __str__(self):
		return self.name
