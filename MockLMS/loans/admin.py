from django.contrib import admin

from .models import LoanAccount


@admin.register(LoanAccount)
class LoanAccountAdmin(admin.ModelAdmin):
    list_display = (
        "loan_account_number",
        "application",
        "sanctioned_amount",
        "disbursed_amount",
        "outstanding_principal",
        "status",
    )
    search_fields = ("loan_account_number", "application__application_number")
    list_filter = ("status",)
