from rest_framework.permissions import AllowAny
from rest_framework.viewsets import ModelViewSet

from .models import LoanAccount
from .serializers import LoanAccountSerializer


class LoanAccountViewSet(ModelViewSet):
    queryset = LoanAccount.objects.select_related(
        "application",
        "application__customer",
        "application__branch",
    ).all()
    serializer_class = LoanAccountSerializer
    authentication_classes = []
    permission_classes = [AllowAny]
    filterset_fields = ["status", "application"]
    search_fields = ["loan_account_number", "application__application_number"]
    ordering_fields = ["loan_account_number", "sanctioned_amount", "created_at"]
