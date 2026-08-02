from django.db import models


class Customer(models.Model):
    customer_number = models.CharField(max_length=40, unique=True, db_index=True)
    first_name = models.CharField(max_length=100, db_index=True)
    last_name = models.CharField(max_length=100, blank=True)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=20, db_index=True)
    date_of_birth = models.DateField(null=True, blank=True)
    branch = models.ForeignKey("branches.Branch", on_delete=models.PROTECT, related_name="customers")
    is_active = models.BooleanField(default=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["first_name", "last_name"]
        constraints = [
            models.UniqueConstraint(fields=["branch", "phone"], name="uq_customer_branch_phone"),
        ]

    def __str__(self) -> str:
        last_name = f" {self.last_name}" if self.last_name else ""
        return f"{self.customer_number} - {self.first_name}{last_name}"
