from django.urls import path
from rest_framework.routers import DefaultRouter

from .views import PermissionViewSet, RoleViewSet, UserDirectoryAPIView

app_name = "identity"

router = DefaultRouter()
router.register("roles", RoleViewSet, basename="role")
router.register("permissions", PermissionViewSet, basename="permission")

urlpatterns = [
	*router.urls,
	path("users", UserDirectoryAPIView.as_view(), name="user-list"),
	path("users/", UserDirectoryAPIView.as_view(), name="user-list-slash"),
]
