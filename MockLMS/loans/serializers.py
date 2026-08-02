from rest_framework import serializers

from applications.models import LoanApplication

from .models import LoanAccount


class LoanApplicationSummarySerializer(serializers.ModelSerializer):
    class Meta:
        model = LoanApplication
        fields = (
            "id",
            "application_number",
            "loan_type",
            "requested_amount",
            "status",
            "submitted_at",
        )


class LoanAccountSerializer(serializers.ModelSerializer):
    application = LoanApplicationSummarySerializer(read_only=True)
    application_id = serializers.PrimaryKeyRelatedField(
        source="application",
        queryset=LoanApplication.objects.all(),
        write_only=True,
    )

    class Meta:
        model = LoanAccount
        fields = (
            "id",
            "loan_account_number",
            "application",
            "application_id",
            "sanctioned_amount",
            "disbursed_amount",
            "outstanding_principal",
            "emi_amount",
            "disbursed_on",
            "status",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("id", "created_at", "updated_at")

    def validate_sanctioned_amount(self, value):
        if value <= 0:
            raise serializers.ValidationError("sanctioned_amount must be greater than zero.")
        return value

    def validate(self, attrs):
        attrs = super().validate(attrs)
        sanctioned_amount = attrs.get("sanctioned_amount")
        if sanctioned_amount is None and self.instance is not None:
            sanctioned_amount = self.instance.sanctioned_amount

        disbursed_amount = attrs.get("disbursed_amount")
        if disbursed_amount is None and self.instance is not None:
            disbursed_amount = self.instance.disbursed_amount

        outstanding_principal = attrs.get("outstanding_principal")
        if outstanding_principal is None and self.instance is not None:
            outstanding_principal = self.instance.outstanding_principal

        if sanctioned_amount is not None and disbursed_amount is not None and disbursed_amount > sanctioned_amount:
            raise serializers.ValidationError(
                {"disbursed_amount": "disbursed_amount cannot exceed sanctioned_amount."}
            )

        if outstanding_principal is not None and outstanding_principal < 0:
            raise serializers.ValidationError(
                {"outstanding_principal": "outstanding_principal cannot be negative."}
            )

        return attrs
