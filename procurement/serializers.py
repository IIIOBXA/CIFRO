from rest_framework import serializers

from procurement.models import PurchaseRequisition, PurchaseRequisitionLine, Supplier


class SupplierSerializer(serializers.ModelSerializer):
    class Meta:
        model = Supplier
        fields = "__all__"


class PurchaseRequisitionLineSerializer(serializers.ModelSerializer):
    material_name = serializers.CharField(source="material.name", read_only=True)
    material_sku = serializers.CharField(source="material.sku", read_only=True)
    quantity_remaining = serializers.SerializerMethodField()

    def get_quantity_remaining(self, obj):
        return obj.quantity_remaining

    class Meta:
        model = PurchaseRequisitionLine
        fields = "__all__"
        read_only_fields = ["quantity_received"]


class PurchaseRequisitionSerializer(serializers.ModelSerializer):
    lines = PurchaseRequisitionLineSerializer(many=True, read_only=True)

    class Meta:
        model = PurchaseRequisition
        fields = "__all__"
        read_only_fields = ["created_at", "approved_at", "approved_by"]


class ReceiveLineSerializer(serializers.Serializer):
    line_id = serializers.IntegerField()
    quantity = serializers.DecimalField(max_digits=14, decimal_places=4, min_value=0)
    location_id = serializers.IntegerField(required=False, allow_null=True)
