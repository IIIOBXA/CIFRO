from django.contrib import admin

from warehouse.models import StockMovement, StorageLocation


@admin.register(StorageLocation)
class StorageLocationAdmin(admin.ModelAdmin):
    list_display = ("code", "description", "is_active")
    search_fields = ("code",)


@admin.register(StockMovement)
class StockMovementAdmin(admin.ModelAdmin):
    list_display = (
        "created_at",
        "material",
        "quantity",
        "movement_type",
        "location",
        "purchase_requisition",
        "reference_order",
    )
    list_filter = ("movement_type",)
    autocomplete_fields = (
        "material",
        "location",
        "reference_order",
        "purchase_requisition",
        "requisition_line",
        "created_by",
    )
