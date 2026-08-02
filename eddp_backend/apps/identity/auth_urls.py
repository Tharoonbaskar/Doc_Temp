from django.urls import path

from .views import (
    AuthChangePasswordAPIView,
    AuthLoginAPIView,
    AuthLogoutAPIView,
    AuthProfileAPIView,
    AuthRefreshAPIView,
    AuthVerifyAPIView,
)

app_name = "auth"

urlpatterns = [
    path("login", AuthLoginAPIView.as_view(), name="login"),
    path("logout", AuthLogoutAPIView.as_view(), name="logout"),
    path("refresh", AuthRefreshAPIView.as_view(), name="refresh"),
    path("verify", AuthVerifyAPIView.as_view(), name="verify"),
    path("profile", AuthProfileAPIView.as_view(), name="profile"),
    path("change-password", AuthChangePasswordAPIView.as_view(), name="change-password"),
]
