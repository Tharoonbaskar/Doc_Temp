from django.contrib import admin

from .models import Branch


@admin.register(Branch)
class BranchAdmin(admin.ModelAdmin):
    list_display = ("branch_code", "name", "city", "state", "is_active", "created_at")
    search_fields = ("branch_code", "name", "city", "state")
    list_filter = ("city", "state", "is_active")
