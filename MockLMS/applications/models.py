from django.db import models


class ApplicationStatus(models.TextChoices):
    DRAFT = "DRAFT", "Draft"
    SUBMITTED = "SUBMITTED", "Submitted"
    UNDER_REVIEW = "UNDER_REVIEW", "Under Review"
    APPROVED = "APPROVED", "Approved"
    REJECTED = "REJECTED", "Rejected"


class LoanType(models.TextChoices):
    HOME = "HOME", "Home Loan"
    PERSONAL = "PERSONAL", "Personal Loan"
    AUTO = "AUTO", "Auto Loan"
    LAP = "LAP", "Loan Against Property"


class LoanApplication(models.Model):
    application_number = models.CharField(max_length=40, unique=True, db_index=True)
    customer = models.ForeignKey("customers.Customer", on_delete=models.PROTECT, related_name="applications")
    branch = models.ForeignKey("branches.Branch", on_delete=models.PROTECT, related_name="applications")
    loan_type = models.CharField(max_length=20, choices=LoanType.choices, db_index=True)
    requested_amount = models.DecimalField(max_digits=14, decimal_places=2)
    tenure_months = models.PositiveIntegerField()
    interest_rate = models.DecimalField(max_digits=5, decimal_places=2)
    status = models.CharField(max_length=20, choices=ApplicationStatus.choices, default=ApplicationStatus.DRAFT, db_index=True)
    remarks = models.TextField(blank=True)
    submitted_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"{self.application_number} ({self.loan_type})"
