from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient

from .models import Rule, RuleGroup


class RulePhaseThreeApiTests(TestCase):
	def setUp(self):
		self.client = APIClient()
		self.user = get_user_model().objects.create_user(
			username="rule_phase3_tester",
			password="password123",
		)
		self.client.force_authenticate(user=self.user)

		self.rule_group = RuleGroup.objects.create(
			code="RULE_GRP_PHASE3",
			name="Phase 3 Rule Group",
			description="Rule group for phase 3 tests",
			priority=10,
		)
		self.rule = Rule.objects.create(
			code="RULE_PHASE3_MAIN",
			rule_group=self.rule_group,
			name="Phase3MainRule",
			description="Main rule used in tests",
			expression="resolved_variables.loan_amount > 1000",
			rule_type="VALIDATION",
			execution_order=1,
			is_active=True,
		)

	def test_rule_registry_list_returns_success_response(self):
		response = self.client.get("/api/rules/rules/")

		self.assertEqual(response.status_code, 200)
		self.assertTrue(response.data["success"])
		self.assertGreaterEqual(len(response.data["data"]), 1)

	def test_rule_registry_search_filters_by_code(self):
		response = self.client.get("/api/rules/rules/", {"search": "RULE_PHASE3_MAIN"})

		self.assertEqual(response.status_code, 200)
		self.assertTrue(response.data["success"])
		self.assertEqual(len(response.data["data"]), 1)
		self.assertEqual(response.data["data"][0]["code"], self.rule.code)
