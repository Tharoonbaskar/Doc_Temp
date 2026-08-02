from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient
from unittest.mock import patch

from apps.documents.models import Document, DocumentCategory

from .models import Template, TemplateVersion


class TemplateRegistryApiTests(TestCase):
	def setUp(self):
		self.client = APIClient()
		self.user = get_user_model().objects.create_user(
			username="template_tester",
			password="password123",
		)
		self.client.force_authenticate(user=self.user)

		self.category = DocumentCategory.objects.create(
			code="DOC_CAT_TMPL",
			name="Template Category",
			description="Template test category",
		)
		self.document = Document.objects.create(
			code="DOC_TEMPLATE_TEST",
			category=self.category,
			name="Template Test Document",
			document_type="FORM",
			business_module="PRIME",
			product="HOME LOAN",
			output_format="PDF",
			description="Document for template tests",
		)
		self.template = Template.objects.create(
			code="TPL_TEST_MAIN",
			name="Template Main",
			description="Primary template",
			category="GENERIC",
			document=self.document,
			template_type="DYNAMIC",
			content_type="application/json",
			is_default=True,
		)
		self.template_version = TemplateVersion.objects.create(
			code="TPL_TEST_VER_1",
			template=self.template,
			version_number=1,
			version_name="v1",
			template_json={"sections": []},
			change_summary="Initial template release",
		)

	def test_template_version_list_endpoint_returns_records(self):
		response = self.client.get("/api/templates/template-versions/")

		self.assertEqual(response.status_code, 200)
		self.assertTrue(response.data["success"])
		self.assertEqual(len(response.data["data"]), 1)
		self.assertEqual(response.data["data"][0]["code"], self.template_version.code)

	def test_template_search_filters_registry_records(self):
		response = self.client.get("/api/templates/templates/", {"search": "Template Main"})

		self.assertEqual(response.status_code, 200)
		self.assertEqual(len(response.data["data"]), 1)
		self.assertEqual(response.data["data"][0]["code"], self.template.code)


class TemplateRenderApiTests(TestCase):
	def setUp(self):
		self.client = APIClient()
		self.user = get_user_model().objects.create_user(
			username="render_tester",
			password="password123",
		)
		self.client.force_authenticate(user=self.user)

		self.category = DocumentCategory.objects.create(
			code="DOC_CAT_RENDER",
			name="Render Category",
			description="Render test category",
		)
		self.document = Document.objects.create(
			code="DOC_RENDER_TEST",
			category=self.category,
			name="Render Test Document",
			document_type="FORM",
			business_module="PRIME",
			product="HOME LOAN",
			output_format="PDF",
			description="Document for render tests",
		)
		self.template = Template.objects.create(
			code="DOC_TESTING_1_TEMPLATE_000001",
			name="TESTING 1",
			description="Template for render service",
			category="GENERIC",
			document=self.document,
			template_type="DYNAMIC",
			content_type="application/json",
			status="APPROVED",
		)
		self.template_version = TemplateVersion.objects.create(
			code="DOC_TESTING_1_TEMPLATE_000001_V1",
			template=self.template,
			version_number=1,
			version_name="v1",
			version_status="APPROVED",
			template_json={
				"type": "doc",
				"content": [
					{
						"type": "paragraph",
						"content": [
							{"type": "text", "text": "Applicant: {{ APPLICANT_NAME }}"},
							{"type": "text", "text": " Customer: {{ CUSTOMER_ID }}"},
						],
					}
				],
			},
		)

	@patch("apps.templates.render_services.html2pdf_renderer.Html2PdfRenderer.render")
	def test_render_api_returns_success_response(self, mocked_render):
		mocked_render.return_value = b"fake-pdf"

		response = self.client.post(
			"/api/v1/templates/render",
			{
				"template_code": "DOC_TESTING_1_TEMPLATE_000001",
				"payload": {
					"APPLICANT_NAME": "THAROON",
					"CUSTOMER_ID": "CUS0004567",
					"LOAN_AMOUNT": "25,00,000",
					"INTEREST_RATE": "9.5%",
				},
				"output": {
					"format": "pdf",
					"response": "base64",
				},
			},
			format="json",
		)

		self.assertEqual(response.status_code, 200)
		self.assertEqual(response.data["status"], "SUCCESS")
		self.assertEqual(response.data["document"]["template_code"], "DOC_TESTING_1_TEMPLATE_000001")
		self.assertEqual(response.data["document"]["mime_type"], "application/pdf")
		self.assertTrue(response.data["document"]["content"])

	@patch("apps.templates.render_services.html2pdf_renderer.Html2PdfRenderer.render")
	def test_render_api_allows_unauthenticated_requests(self, mocked_render):
		mocked_render.return_value = b"fake-pdf"
		anonymous_client = APIClient()

		response = anonymous_client.post(
			"/api/v1/templates/render",
			{
				"template_code": "DOC_TESTING_1_TEMPLATE_000001",
				"payload": {
					"APPLICANT_NAME": "THAROON",
					"CUSTOMER_ID": "CUS0004567",
				},
				"output": {
					"format": "pdf",
					"response": "base64",
				},
			},
			format="json",
		)

		self.assertEqual(response.status_code, 200)
		self.assertEqual(response.data["status"], "SUCCESS")

	@patch("apps.templates.render_services.html2pdf_renderer.Html2PdfRenderer.render")
	def test_render_api_returns_missing_variable_response(self, mocked_render):
		mocked_render.return_value = b"fake-pdf"

		response = self.client.post(
			"/api/v1/templates/render",
			{
				"template_code": "DOC_TESTING_1_TEMPLATE_000001",
				"payload": {
					"APPLICANT_NAME": "THAROON",
				},
				"output": {
					"format": "pdf",
					"response": "base64",
				},
			},
			format="json",
		)

		self.assertEqual(response.status_code, 400)
		self.assertEqual(response.data["status"], "FAILED")
		self.assertEqual(response.data["message"], "Required template variables are missing.")
		self.assertIn("CUSTOMER_ID", response.data["missing_variables"])

	def test_render_api_returns_template_not_found(self):
		response = self.client.post(
			"/api/v1/templates/render",
			{
				"template_code": "NOT_FOUND_TEMPLATE",
				"payload": {
					"APPLICANT_NAME": "THAROON",
				},
				"output": {
					"format": "pdf",
					"response": "base64",
				},
			},
			format="json",
		)

		self.assertEqual(response.status_code, 404)
		self.assertEqual(response.data["status"], "FAILED")
		self.assertEqual(response.data["message"], "Template not found.")

	@patch("apps.templates.render_services.html2pdf_renderer.Html2PdfRenderer.render")
	def test_render_api_supports_nested_template_code_shape(self, mocked_render):
		mocked_render.return_value = b"fake-pdf"

		response = self.client.post(
			"/api/v1/templates/render",
			{
				"template": {
					"code": "DOC_TESTING_1_TEMPLATE_000001",
				},
				"payload": {
					"APPLICANT_NAME": "THAROON",
					"CUSTOMER_ID": "CUS0004567",
					"LOAN_AMOUNT": "25,00,000",
					"INTEREST_RATE": "9.5%",
				},
				"output": {
					"format": "pdf",
					"response": "base64",
				},
			},
			format="json",
		)

		self.assertEqual(response.status_code, 200)
		self.assertEqual(response.data["status"], "SUCCESS")
		self.assertEqual(response.data["document"]["template_code"], "DOC_TESTING_1_TEMPLATE_000001")

	def test_render_api_returns_template_not_approved(self):
		self.template_version.version_status = "DRAFT"
		self.template_version.save(update_fields=["version_status"])

		response = self.client.post(
			"/api/v1/templates/render",
			{
				"template_code": "DOC_TESTING_1_TEMPLATE_000001",
				"payload": {
					"APPLICANT_NAME": "THAROON",
					"CUSTOMER_ID": "CUS0004567",
				},
				"output": {
					"format": "pdf",
					"response": "base64",
				},
			},
			format="json",
		)

		self.assertEqual(response.status_code, 400)
		self.assertEqual(response.data["status"], "FAILED")
		self.assertEqual(response.data["message"], "No approved template version available.")
