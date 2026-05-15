import io

from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import decorators, response, viewsets

from catalog.models import Material
from warehouse.models import StockMovement, StorageLocation
from warehouse.serializers import StockMovementSerializer, StorageLocationSerializer


class StorageLocationViewSet(viewsets.ModelViewSet):
    queryset = StorageLocation.objects.all()
    serializer_class = StorageLocationSerializer
    filterset_fields = ["is_active"]
    search_fields = ["code", "description"]


class StockMovementViewSet(viewsets.ModelViewSet):
    queryset = StockMovement.objects.select_related("material", "location", "reference_order")
    serializer_class = StockMovementSerializer
    filterset_fields = ["material", "location", "movement_type", "reference_order"]


@decorators.api_view(["GET"])
def material_qr_png(request, sku: str):
    """QR-код по SKU материала (для печати / сканирования телефоном)."""
    import qrcode

    material = get_object_or_404(Material, sku=sku)
    img = qrcode.make(material.sku)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return HttpResponse(buf.getvalue(), content_type="image/png")
