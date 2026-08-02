from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient


class RuntimePhaseThreeValidationTests(TestCase):
	def setUp(self):
		self.client = APIClient()
		self.user = get_user_model().objects.create_user(
			username="runtime_phase3_tester",
			password="password123",
		)
		self.client.force_authenticate(user=self.user)

	def test_execute_rules_requires_rule_group_code(self):
		response = self.client.post("/api/runtime/execute-rules", {}, format="json")

		self.assertEqual(response.status_code, 400)
		self.assertFalse(response.data.get("success", True))

	def test_resolve_variables_requires_mandatory_fields(self):
		response = self.client.post("/api/runtime/resolve-variables", {}, format="json")

		self.assertEqual(response.status_code, 400)
		self.assertFalse(response.data.get("success", True))
