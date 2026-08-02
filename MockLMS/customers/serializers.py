from rest_framework import serializers

from branches.models import Branch

from .models import Customer


class BranchSummarySerializer(serializers.ModelSerializer):
    class Meta:
        model = Branch
        fields = ("id", "branch_code", "name", "city", "state")


class CustomerSerializer(serializers.ModelSerializer):
    branch = BranchSummarySerializer(read_only=True)
    branch_id = serializers.PrimaryKeyRelatedField(source="branch", queryset=Branch.objects.all(), write_only=True)

    class Meta:
        model = Customer
        fields = (
            "id",
            "customer_number",
            "first_name",
            "last_name",
            "email",
            "phone",
            "date_of_birth",
            "branch",
            "branch_id",
            "is_active",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("id", "created_at", "updated_at")

    def validate_phone(self, value: str) -> str:
        normalized = "".join(ch for ch in value if ch.isdigit() or ch == "+")
        if not normalized:
            raise serializers.ValidationError("Phone is required.")
        return normalized
