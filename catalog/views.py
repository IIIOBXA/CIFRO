from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets

from catalog.models import BillOfMaterialLine, Material, ProductTemplate
from catalog.serializers import (
    BillOfMaterialLineSerializer,
    MaterialSerializer,
    ProductTemplateSerializer,
)


class MaterialViewSet(viewsets.ModelViewSet):
    queryset = Material.objects.all()
    serializer_class = MaterialSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["is_active"]
    search_fields = ["sku", "name"]


class ProductTemplateViewSet(viewsets.ModelViewSet):
    queryset = ProductTemplate.objects.all()
    serializer_class = ProductTemplateSerializer
    filterset_fields = ["is_active"]
    search_fields = ["code", "name"]


class BillOfMaterialLineViewSet(viewsets.ModelViewSet):
    queryset = BillOfMaterialLine.objects.select_related("product", "material")
    serializer_class = BillOfMaterialLineSerializer
    filterset_fields = ["product", "material"]
