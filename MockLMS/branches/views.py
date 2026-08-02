from rest_framework.permissions import AllowAny
from rest_framework.viewsets import ModelViewSet

from .models import Branch
from .serializers import BranchSerializer


class BranchViewSet(ModelViewSet):
    queryset = Branch.objects.all()
    serializer_class = BranchSerializer
    authentication_classes = []
    permission_classes = [AllowAny]
    filterset_fields = ["city", "state", "is_active"]
    search_fields = ["branch_code", "name", "city", "state"]
    ordering_fields = ["branch_code", "name", "city", "created_at"]
