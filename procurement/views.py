from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import decorators, response, status, viewsets

from procurement.models import PurchaseRequisition, PurchaseRequisitionLine, Supplier
from procurement.serializers import (
    PurchaseRequisitionLineSerializer,
    PurchaseRequisitionSerializer,
    ReceiveLineSerializer,
    SupplierSerializer,
)
from procurement.services import ReceiveError, open_requisitions_queryset, receive_requisition_bulk


class SupplierViewSet(viewsets.ModelViewSet):
    queryset = Supplier.objects.filter(is_active=True)
    serializer_class = SupplierSerializer
    filterset_fields = ["is_active"]
    search_fields = ["name", "phone", "email"]


class PurchaseRequisitionViewSet(viewsets.ModelViewSet):
    queryset = PurchaseRequisition.objects.select_related("order", "approved_by").prefetch_related(
        "lines__material"
    )
    serializer_class = PurchaseRequisitionSerializer
    filterset_fields = ["status", "order"]

    @decorators.action(detail=False, methods=["get"])
    def open(self, request):
        qs = open_requisitions_queryset()
        page = self.paginate_queryset(qs)
        ser = self.get_serializer(page or qs, many=True)
        if page is not None:
            return self.get_paginated_response(ser.data)
        return response.Response(ser.data)

    @decorators.action(detail=True, methods=["post"])
    def receive(self, request, pk=None):
        """Принять материалы на склад по заявке. Body: {lines: [{line_id, quantity}], location_id?}"""
        requisition = self.get_object()
        lines_data = request.data.get("lines", [])
        if not lines_data:
            return response.Response({"detail": "Укажите lines: [{line_id, quantity}, ...]"}, status=400)
        quantities = {}
        for item in lines_data:
            ser = ReceiveLineSerializer(data=item)
            ser.is_valid(raise_exception=True)
            quantities[ser.validated_data["line_id"]] = ser.validated_data["quantity"]
        location_id = request.data.get("location_id")
        try:
            movements = receive_requisition_bulk(
                requisition,
                quantities,
                location_id=location_id,
                user=request.user,
            )
        except ReceiveError as exc:
            return response.Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        requisition.refresh_from_db()
        return response.Response(
            {
                "movements_count": len(movements),
                "requisition": PurchaseRequisitionSerializer(requisition).data,
            }
        )


class PurchaseRequisitionLineViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = PurchaseRequisitionLine.objects.select_related("requisition", "material", "suggested_supplier")
    serializer_class = PurchaseRequisitionLineSerializer
    filterset_fields = ["requisition", "material"]
