from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient

from .models import Variable, VariableCategory, VariableGroup


class VariablePhaseThreeApiTests(TestCase):
	def setUp(self):
		self.client = APIClient()
		self.user = get_user_model().objects.create_user(
			username="variable_phase3_tester",
			password="password123",
		)
		self.client.force_authenticate(user=self.user)

		self.category = VariableCategory.objects.create(
			code="VAR_CAT_PHASE3",
			name="Phase 3 Variable Category",
			description="Category for phase 3 variable tests",
		)
		self.group = VariableGroup.objects.create(
			code="VAR_GRP_PHASE3",
			name="Phase 3 Variable Group",
			description="Group for phase 3 variable tests",
			category=self.category,
		)
		self.variable = Variable.objects.create(
			code="VAR_PHASE3_MAIN",
			group=self.group,
			name="loan_amount",
			display_name="Loan Amount",
			description="Loan amount input",
			data_type="DECIMAL",
			source_type="INPUT",
			source_reference="payload.loan_amount",
			default_value="0",
			is_required=True,
		)

	def test_variable_registry_list_returns_success_response(self):
		response = self.client.get("/api/variables/variables/")

		self.assertEqual(response.status_code, 200)
		self.assertTrue(response.data["success"])
		self.assertGreaterEqual(len(response.data["data"]), 1)

	def test_variable_registry_search_filters_by_code(self):
		response = self.client.get("/api/variables/variables/", {"search": "VAR_PHASE3_MAIN"})

		self.assertEqual(response.status_code, 200)
		self.assertTrue(response.data["success"])
		self.assertEqual(len(response.data["data"]), 1)
		self.assertEqual(response.data["data"][0]["code"], self.variable.code)
