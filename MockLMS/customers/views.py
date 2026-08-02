from rest_framework.permissions import AllowAny
from rest_framework.viewsets import ModelViewSet

from .models import Customer
from .serializers import CustomerSerializer


class CustomerViewSet(ModelViewSet):
    queryset = Customer.objects.select_related("branch").all()
    serializer_class = CustomerSerializer
    authentication_classes = []
    permission_classes = [AllowAny]
    filterset_fields = ["branch", "is_active"]
    search_fields = ["customer_number", "first_name", "last_name", "phone", "email"]
    ordering_fields = ["customer_number", "first_name", "created_at"]
