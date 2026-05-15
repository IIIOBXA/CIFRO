from django.contrib import admin

from procurement.models import PurchaseRequisition, PurchaseRequisitionLine, Supplier


class LineInline(admin.TabularInline):
    model = PurchaseRequisitionLine
    extra = 0
    readonly_fields = ("quantity_received",)
    autocomplete_fields = ("material", "suggested_supplier")


@admin.register(Supplier)
class SupplierAdmin(admin.ModelAdmin):
    list_display = ("name", "lead_time_days", "phone", "is_active")
    search_fields = ("name", "phone", "email")


@admin.register(PurchaseRequisition)
class PurchaseRequisitionAdmin(admin.ModelAdmin):
    list_display = ("id", "title", "order", "status", "created_at")
    list_filter = ("status",)
    search_fields = ("title",)
    inlines = [LineInline]
    autocomplete_fields = ("order", "approved_by")


@admin.register(PurchaseRequisitionLine)
class PurchaseRequisitionLineAdmin(admin.ModelAdmin):
    list_display = ("requisition", "material", "quantity_required", "quantity_received", "suggested_supplier")
    search_fields = ("material__sku", "material__name", "requisition__title")
    autocomplete_fields = ("requisition", "material", "suggested_supplier")
