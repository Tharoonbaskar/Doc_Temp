from django.urls import include, path

from api.views import HealthCheckAPIView

urlpatterns = [
    path("health", HealthCheckAPIView.as_view(), name="health"),
    path("", include("branches.urls")),
    path("", include("customers.urls")),
    path("", include("applications.urls")),
    path("", include("loans.urls")),
]
