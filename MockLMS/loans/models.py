from django.db import models


class LoanStatus(models.TextChoices):
    ACTIVE = "ACTIVE", "Active"
    CLOSED = "CLOSED", "Closed"
    DEFAULTED = "DEFAULTED", "Defaulted"


class LoanAccount(models.Model):
    loan_account_number = models.CharField(max_length=40, unique=True, db_index=True)
    application = models.OneToOneField(
        "applications.LoanApplication",
        on_delete=models.PROTECT,
        related_name="loan_account",
    )
    sanctioned_amount = models.DecimalField(max_digits=14, decimal_places=2)
    disbursed_amount = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    outstanding_principal = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    emi_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    disbursed_on = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=LoanStatus.choices, default=LoanStatus.ACTIVE, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return self.loan_account_number
