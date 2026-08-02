from django.contrib import admin

from .models import Customer


@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ("customer_number", "first_name", "last_name", "phone", "branch", "is_active")
    search_fields = ("customer_number", "first_name", "last_name", "phone", "email")
    list_filter = ("branch", "is_active")
