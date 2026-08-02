from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient

from .models import Permission, Role, UserRole


class IdentityAdministrationApiTests(TestCase):
	def setUp(self):
		self.client = APIClient()
		self.admin_user = get_user_model().objects.create_user(
			username="identity_admin",
			password="password123",
			first_name="Identity",
			last_name="Admin",
			email="identity.admin@example.com",
		)
		self.client.force_authenticate(user=self.admin_user)

	def test_permissions_endpoint_returns_permission_catalog(self):
		Permission.objects.create(
			code="PERM_RUNTIME_READ",
			module="RUNTIME",
			action="READ",
			description="Read runtime records",
		)

		response = self.client.get("/api/identity/permissions/")

		self.assertEqual(response.status_code, 200)
		self.assertTrue(response.data["success"])
		self.assertEqual(len(response.data["data"]), 1)
		self.assertEqual(response.data["data"][0]["code"], "PERM_RUNTIME_READ")

	def test_users_endpoint_returns_users_with_roles(self):
		role = Role.objects.create(
			code="ROLE_MAKER",
			name="Maker",
			description="Maker role",
		)
		user = get_user_model().objects.create_user(
			username="maker.user",
			password="password123",
			first_name="Maker",
			last_name="User",
			email="maker.user@example.com",
			is_active=True,
		)
		UserRole.objects.create(
			code="USRROLE_MAKER_1",
			user=user,
			role=role,
		)

		response = self.client.get("/api/identity/users", {"search": "maker.user"})

		self.assertEqual(response.status_code, 200)
		self.assertTrue(response.data["success"])
		self.assertEqual(len(response.data["data"]), 1)
		self.assertEqual(response.data["data"][0]["username"], "maker.user")
		self.assertIn("Maker", response.data["data"][0]["roles"])
