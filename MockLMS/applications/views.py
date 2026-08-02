from rest_framework.permissions import AllowAny
from rest_framework.viewsets import ModelViewSet

from .models import LoanApplication
from .serializers import LoanApplicationSerializer


class LoanApplicationViewSet(ModelViewSet):
    queryset = LoanApplication.objects.select_related("customer", "branch").all()
    serializer_class = LoanApplicationSerializer
    authentication_classes = []
    permission_classes = [AllowAny]
    filterset_fields = ["loan_type", "status", "branch", "customer"]
    search_fields = ["application_number", "remarks", "customer__customer_number", "customer__first_name"]
    ordering_fields = ["application_number", "requested_amount", "created_at", "submitted_at"]
