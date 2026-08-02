from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient

from .models import Document, DocumentCategory, DocumentDefinition


class DocumentRegistryApiTests(TestCase):
	def setUp(self):
		self.client = APIClient()
		self.user = get_user_model().objects.create_user(
			username="doc_tester",
			password="password123",
		)
		self.client.force_authenticate(user=self.user)

		self.category = DocumentCategory.objects.create(
			code="DOC_CAT_TEST",
			name="Testing Category",
			description="Test category",
		)

		self.document = Document.objects.create(
			code="DOC_HOME_LOAN",
			category=self.category,
			name="Home Loan Sanction",
			document_type="LETTER",
			business_module="PRIME",
			product="HOME LOAN",
			output_format="PDF",
			description="Document for sanction letter",
		)

		self.definition = DocumentDefinition.objects.create(
			code="DOC_DEF_HOME_LOAN",
			document=self.document,
			active_template_code="TPL_SANCTION_V1",
			variable_group_code="VAR_GRP_SANCTION",
			connector_code="CONN_CORE_API",
			rule_group_code="RULE_GRP_SANCTION",
			language="en",
			effective_from=timezone.now(),
		)

	def test_document_definition_list_endpoint_returns_records(self):
		response = self.client.get("/api/documents/document-definitions/")

		self.assertEqual(response.status_code, 200)
		self.assertTrue(response.data["success"])
		self.assertEqual(len(response.data["data"]), 1)
		self.assertEqual(response.data["data"][0]["code"], self.definition.code)

	def test_document_definition_search_filters_records(self):
		response = self.client.get(
			"/api/documents/document-definitions/",
			{"search": "TPL_SANCTION_V1"},
		)

		self.assertEqual(response.status_code, 200)
		self.assertEqual(len(response.data["data"]), 1)
		self.assertEqual(response.data["data"][0]["code"], self.definition.code)

	def test_document_search_filters_registry_records(self):
		response = self.client.get("/api/documents/documents/", {"search": "HOME LOAN"})

		self.assertEqual(response.status_code, 200)
		self.assertEqual(len(response.data["data"]), 1)
		self.assertEqual(response.data["data"][0]["code"], self.document.code)
