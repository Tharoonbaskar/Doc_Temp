from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient

from apps.documents.models import Document, DocumentCategory
from apps.runtime.models import GeneratedDocument, GenerationRequest
from apps.templates.models import Template, TemplateVersion

from .models import ActivityLog, Snapshot


class GovernanceApiTests(TestCase):
	def setUp(self):
		self.client = APIClient()
		self.user = get_user_model().objects.create_user(
			username="governance_tester",
			password="password123",
		)
		self.client.force_authenticate(user=self.user)

		self.category = DocumentCategory.objects.create(
			code="DOC_CAT_GOV",
			name="Governance Category",
			description="Governance docs",
		)
		self.document = Document.objects.create(
			code="DOC_GOV_SAMPLE",
			category=self.category,
			name="Governance Sample",
			document_type="REPORT",
			business_module="PRIME",
			product="HOME LOAN",
			output_format="PDF",
			description="Governance testing document",
		)
		self.template = Template.objects.create(
			code="TPL_GOV_SAMPLE",
			name="Governance Template",
			description="Template for governance tests",
			category="GENERIC",
			document=self.document,
			template_type="DYNAMIC",
			content_type="application/json",
			is_default=True,
		)
		self.template_version = TemplateVersion.objects.create(
			code="TPL_VER_GOV_1",
			template=self.template,
			version_number=1,
			version_name="v1",
			template_json={"blocks": []},
			change_summary="Initial version",
		)
		self.generation_request = GenerationRequest.objects.create(
			code="GEN_REQ_GOV_1",
			document=self.document,
			template_version=self.template_version,
			request_source="API",
			business_reference="REF-GOV-001",
			input_payload={"customer": "Jane"},
			requested_by=self.user,
		)
		self.generated_document = GeneratedDocument.objects.create(
			code="GEN_DOC_GOV_1",
			generation_request=self.generation_request,
			file_name="governance-test.pdf",
			file_path="media/generated/governance-test.pdf",
			file_type="PDF",
			file_size=1024,
			checksum="abc123checksum",
		)

	def test_activity_logs_endpoint_returns_records(self):
		ActivityLog.objects.create(
			code="ACT_GOV_1",
			module="RUNTIME",
			activity="DOCUMENT_GENERATED",
			reference_number="REF-GOV-001",
			description="Generated sample document",
			performed_by=self.user,
		)

		response = self.client.get("/api/governance/activity-logs/")

		self.assertEqual(response.status_code, 200)
		self.assertTrue(response.data["success"])
		self.assertEqual(len(response.data["data"]), 1)
		self.assertEqual(response.data["data"][0]["code"], "ACT_GOV_1")

	def test_snapshots_endpoint_returns_records(self):
		Snapshot.objects.create(
			code="SNP_GOV_1",
			generated_document=self.generated_document,
			snapshot_version=1,
			snapshot_json={"request_id": str(self.generation_request.request_id)},
		)

		response = self.client.get("/api/governance/snapshots/")

		self.assertEqual(response.status_code, 200)
		self.assertTrue(response.data["success"])
		self.assertEqual(len(response.data["data"]), 1)
		self.assertEqual(response.data["data"][0]["code"], "SNP_GOV_1")
		self.assertEqual(response.data["data"][0]["generated_document"]["code"], "GEN_DOC_GOV_1")
