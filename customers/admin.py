from django.contrib import admin

from customers.models import Customer


@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ("name", "organization", "phone", "email", "payment_status", "is_active")
    list_filter = ("payment_status", "is_active")
    search_fields = ("name", "organization", "phone", "email")
