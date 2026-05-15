from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

from orders.models import OrderStatus
from procurement.models import PurchaseRequisition, RequisitionStatus
from procurement.services import ReceiveError, open_requisitions_queryset, receive_requisition_bulk
from warehouse.forms import ReceiveRequisitionForm


@login_required
def requisition_list(request):
    return render(
        request,
        "warehouse/requisition_list.html",
        {"requisitions": open_requisitions_queryset()},
    )


@login_required
def requisition_receive(request, pk: int):
    requisition = get_object_or_404(
        PurchaseRequisition.objects.select_related("order", "order__customer").prefetch_related(
            "lines__material"
        ),
        pk=pk,
    )
    lines = list(requisition.lines.all())
    pending_lines = [ln for ln in lines if ln.quantity_remaining > 0]

    if not pending_lines:
        messages.info(request, "По этой заявке всё уже принято на склад.")
        if requisition.order_id:
            return redirect("order-detail", pk=requisition.order_id)
        return redirect("warehouse-requisition-list")

    form = ReceiveRequisitionForm(requisition, request.POST or None)
    if request.method == "POST" and form.is_valid():
        quantities = form.line_quantities()
        if not quantities:
            messages.warning(request, "Укажите количество хотя бы по одной позиции.")
        else:
            location = form.cleaned_data.get("location")
            try:
                movements = receive_requisition_bulk(
                    requisition,
                    quantities,
                    location_id=location.pk if location else None,
                    user=request.user,
                )
                messages.success(
                    request,
                    f"Принято на склад: {len(movements)} позиций.",
                )
                requisition.refresh_from_db()
                if requisition.status == RequisitionStatus.RECEIVED:
                    messages.success(request, "Заявка полностью выполнена.")
                if requisition.order_id:
                    requisition.order.refresh_from_db()
                    if requisition.order.status == OrderStatus.PRODUCTION:
                        messages.success(
                            request,
                            f"Заказ №{requisition.order_id}: материалов достаточно — «В производстве».",
                        )
                    return redirect("order-detail", pk=requisition.order_id)
                return redirect("warehouse-requisition-list")
            except ReceiveError as exc:
                messages.error(request, str(exc))

    return render(
        request,
        "warehouse/requisition_receive.html",
        {
            "requisition": requisition,
            "form": form,
            "pending_lines": pending_lines,
            "all_lines": lines,
        },
    )
