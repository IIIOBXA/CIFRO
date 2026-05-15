from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import decorators, response, viewsets

from orders.models import Order
from orders.planning import build_order_plan
from orders.serializers import OrderSerializer
from orders.services import confirm_order_and_plan_procurement


class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.select_related("customer", "product_template", "created_by")
    serializer_class = OrderSerializer
    filterset_fields = ["status", "customer", "product_template"]
    search_fields = ["internal_number", "notes"]

    @decorators.action(detail=True, methods=["get"])
    def requirements(self, request, pk=None):
        plan = build_order_plan(self.get_object())
        return response.Response(
            {
                "materials": {
                    str(mid): {"required": str(plan.need[mid]), "on_hand": str(plan.balances.get(mid, 0))}
                    for mid in plan.need
                }
            }
        )

    @decorators.action(detail=True, methods=["get"])
    def shortage(self, request, pk=None):
        plan = build_order_plan(self.get_object())
        return response.Response({"shortage": {str(k): str(v) for k, v in plan.shortage.items()}})

    @decorators.action(detail=True, methods=["post"])
    def confirm(self, request, pk=None):
        result = confirm_order_and_plan_procurement(self.get_object())
        result.order.refresh_from_db()
        data = {
            "order": OrderSerializer(result.order, context={"request": request}).data,
            "created_requisition": result.created_requisition,
            "updated_requisition": result.updated_requisition,
        }
        if result.requisition:
            from procurement.serializers import PurchaseRequisitionSerializer

            data["purchase_requisition"] = PurchaseRequisitionSerializer(
                result.requisition, context={"request": request}
            ).data
        return response.Response(data)
