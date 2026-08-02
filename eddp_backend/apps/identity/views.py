from __future__ import annotations

from drf_spectacular.utils import OpenApiResponse, extend_schema
from rest_framework.permissions import AllowAny
from rest_framework.views import APIView
from rest_framework_simplejwt.authentication import JWTAuthentication

from apps.common.permissions import IsAuthenticatedUser
from apps.common.views import EnterpriseServiceViewSet

from .serializers import (
	AuthLoginSerializer,
	AuthLogoutSerializer,
	AuthRefreshSerializer,
	AuthVerifySerializer,
	ChangePasswordSerializer,
	PermissionSerializer,
	ProfileUpdateSerializer,
	RoleSerializer,
)
from .services import (
	AuthenticationService,
	IdentityService,
	PermissionCatalogService,
	UserDirectoryService,
)


class RoleViewSet(EnterpriseServiceViewSet):
	service_class = IdentityService
	serializer_class = RoleSerializer


class PermissionViewSet(EnterpriseServiceViewSet):
	service_class = PermissionCatalogService
	serializer_class = PermissionSerializer


class UserDirectoryAPIView(APIView):
	authentication_classes = [JWTAuthentication]
	permission_classes = [IsAuthenticatedUser]

	@extend_schema(
		responses={200: OpenApiResponse(description="Users fetched")},
		tags=["Identity"],
	)
	def get(self, request, *args, **kwargs):
		service = UserDirectoryService()
		return service.get_all(
			query_params=EnterpriseServiceViewSet._normalized_query_params(request.query_params)
		)


class AuthLoginAPIView(APIView):
	authentication_classes = []
	permission_classes = [AllowAny]

	@extend_schema(
		request=AuthLoginSerializer,
		responses={200: OpenApiResponse(description="Login successful")},
		tags=["Authentication"],
	)
	def post(self, request, *args, **kwargs):
		serializer = AuthLoginSerializer(data=request.data)
		serializer.is_valid(raise_exception=True)
		service = AuthenticationService()
		return service.login(
			request=request,
			username=serializer.validated_data["username"],
			password=serializer.validated_data["password"],
		)


class AuthLogoutAPIView(APIView):
	authentication_classes = [JWTAuthentication]
	permission_classes = [IsAuthenticatedUser]

	@extend_schema(
		request=AuthLogoutSerializer,
		responses={200: OpenApiResponse(description="Logout successful")},
		tags=["Authentication"],
	)
	def post(self, request, *args, **kwargs):
		serializer = AuthLogoutSerializer(data=request.data)
		serializer.is_valid(raise_exception=True)
		service = AuthenticationService()
		return service.logout(request=request, refresh_token=serializer.validated_data["refresh"])


class AuthRefreshAPIView(APIView):
	authentication_classes = []
	permission_classes = [AllowAny]

	@extend_schema(
		request=AuthRefreshSerializer,
		responses={200: OpenApiResponse(description="Token refreshed")},
		tags=["Authentication"],
	)
	def post(self, request, *args, **kwargs):
		serializer = AuthRefreshSerializer(data=request.data)
		serializer.is_valid(raise_exception=True)
		service = AuthenticationService()
		return service.refresh_token(request=request, refresh_token=serializer.validated_data["refresh"])


class AuthVerifyAPIView(APIView):
	authentication_classes = []
	permission_classes = [AllowAny]

	@extend_schema(
		request=AuthVerifySerializer,
		responses={200: OpenApiResponse(description="Token verification result")},
		tags=["Authentication"],
	)
	def post(self, request, *args, **kwargs):
		serializer = AuthVerifySerializer(data=request.data)
		serializer.is_valid(raise_exception=True)
		service = AuthenticationService()
		return service.verify_token(token=serializer.validated_data["token"])


class AuthProfileAPIView(APIView):
	authentication_classes = [JWTAuthentication]
	permission_classes = [IsAuthenticatedUser]

	@extend_schema(
		responses={200: OpenApiResponse(description="Profile details")},
		tags=["Authentication"],
	)
	def get(self, request, *args, **kwargs):
		service = AuthenticationService()
		return service.get_current_user(user=request.user)

	@extend_schema(
		request=ProfileUpdateSerializer,
		responses={200: OpenApiResponse(description="Profile updated")},
		tags=["Authentication"],
	)
	def put(self, request, *args, **kwargs):
		serializer = ProfileUpdateSerializer(data=request.data)
		serializer.is_valid(raise_exception=True)
		service = AuthenticationService()
		return service.update_current_user(user=request.user, profile_data=dict(serializer.validated_data))


class AuthChangePasswordAPIView(APIView):
	authentication_classes = [JWTAuthentication]
	permission_classes = [IsAuthenticatedUser]

	@extend_schema(
		request=ChangePasswordSerializer,
		responses={200: OpenApiResponse(description="Password changed")},
		tags=["Authentication"],
	)
	def post(self, request, *args, **kwargs):
		serializer = ChangePasswordSerializer(data=request.data, context={"request": request})
		serializer.is_valid(raise_exception=True)
		service = AuthenticationService()
		return service.change_password(
			request=request,
			user=request.user,
			current_password=serializer.validated_data["current_password"],
			new_password=serializer.validated_data["new_password"],
		)
