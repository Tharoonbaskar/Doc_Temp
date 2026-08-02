from django.contrib import admin

from .models import LoanApplication


@admin.register(LoanApplication)
class LoanApplicationAdmin(admin.ModelAdmin):
    list_display = (
        "application_number",
        "customer",
        "branch",
        "loan_type",
        "requested_amount",
        "status",
        "created_at",
    )
    search_fields = ("application_number", "customer__customer_number", "customer__first_name")
    list_filter = ("loan_type", "status", "branch")
