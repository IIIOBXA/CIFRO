from django.contrib import admin

from orders.models import Order


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ("id", "customer", "product_template", "quantity", "status", "created_at")
    list_filter = ("status", "product_template")
    autocomplete_fields = ("customer", "product_template", "created_by")
    search_fields = ("internal_number", "notes")
