from django.db import models


class Branch(models.Model):
    branch_code = models.CharField(max_length=30, unique=True, db_index=True)
    name = models.CharField(max_length=150, db_index=True)
    city = models.CharField(max_length=120, db_index=True)
    state = models.CharField(max_length=120)
    is_active = models.BooleanField(default=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]

    def __str__(self) -> str:
        return f"{self.branch_code} - {self.name}"
