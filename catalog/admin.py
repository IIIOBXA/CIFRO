from django.contrib import admin

from catalog.models import BillOfMaterialLine, Material, ProductTemplate


@admin.register(Material)
class MaterialAdmin(admin.ModelAdmin):
    list_display = ("sku", "name", "unit", "min_quantity", "is_active")
    search_fields = ("sku", "name")


class BillInline(admin.TabularInline):
    model = BillOfMaterialLine
    extra = 0


@admin.register(ProductTemplate)
class ProductTemplateAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "is_active")
    search_fields = ("code", "name")
    inlines = [BillInline]


@admin.register(BillOfMaterialLine)
class BillOfMaterialLineAdmin(admin.ModelAdmin):
    list_display = ("product", "material", "quantity_per_unit")
    list_filter = ("product",)
