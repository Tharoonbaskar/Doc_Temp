from rest_framework import serializers

from branches.models import Branch
from customers.models import Customer

from .models import LoanApplication


class BranchSummarySerializer(serializers.ModelSerializer):
    class Meta:
        model = Branch
        fields = ("id", "branch_code", "name", "city", "state")


class CustomerSummarySerializer(serializers.ModelSerializer):
    class Meta:
        model = Customer
        fields = ("id", "customer_number", "first_name", "last_name", "phone")


class LoanApplicationSerializer(serializers.ModelSerializer):
    customer = CustomerSummarySerializer(read_only=True)
    customer_id = serializers.PrimaryKeyRelatedField(source="customer", queryset=Customer.objects.all(), write_only=True)
    branch = BranchSummarySerializer(read_only=True)
    branch_id = serializers.PrimaryKeyRelatedField(source="branch", queryset=Branch.objects.all(), write_only=True)

    class Meta:
        model = LoanApplication
        fields = (
            "id",
            "application_number",
            "customer",
            "customer_id",
            "branch",
            "branch_id",
            "loan_type",
            "requested_amount",
            "tenure_months",
            "interest_rate",
            "status",
            "remarks",
            "submitted_at",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("id", "created_at", "updated_at")

    def validate_requested_amount(self, value):
        if value <= 0:
            raise serializers.ValidationError("requested_amount must be greater than zero.")
        return value

    def validate_tenure_months(self, value: int) -> int:
        if value <= 0:
            raise serializers.ValidationError("tenure_months must be greater than zero.")
        return value

    def validate_interest_rate(self, value):
        if value <= 0:
            raise serializers.ValidationError("interest_rate must be greater than zero.")
        return value

    def validate(self, attrs):
        attrs = super().validate(attrs)
        customer = attrs.get("customer") or getattr(self.instance, "customer", None)
        branch = attrs.get("branch") or getattr(self.instance, "branch", None)

        if customer and branch and customer.branch_id != branch.id:
            raise serializers.ValidationError(
                {"branch_id": "branch_id must match the customer's home branch."}
            )

        return attrs
