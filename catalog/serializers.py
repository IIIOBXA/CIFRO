from rest_framework import serializers

from catalog.models import BillOfMaterialLine, Material, ProductTemplate


class MaterialSerializer(serializers.ModelSerializer):
    class Meta:
        model = Material
        fields = "__all__"


class ProductTemplateSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductTemplate
        fields = "__all__"


class BillOfMaterialLineSerializer(serializers.ModelSerializer):
    material_detail = MaterialSerializer(source="material", read_only=True)

    class Meta:
        model = BillOfMaterialLine
        fields = "__all__"
