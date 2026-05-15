from rest_framework import serializers

from orders.models import Order


class OrderSerializer(serializers.ModelSerializer):
    customer_name = serializers.CharField(source="customer.name", read_only=True)
    product_name = serializers.CharField(source="product_template.name", read_only=True)

    class Meta:
        model = Order
        fields = "__all__"
        read_only_fields = ["created_at", "updated_at", "created_by"]

    def create(self, validated_data):
        request = self.context.get("request")
        if request and request.user.is_authenticated:
            validated_data["created_by"] = request.user
        return super().create(validated_data)
