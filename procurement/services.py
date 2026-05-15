from __future__ import annotations

from decimal import Decimal

from django.db import transaction

from orders.models import Order, OrderStatus
from orders.planning import build_order_plan
from procurement.models import PurchaseRequisition, PurchaseRequisitionLine, RequisitionStatus
from warehouse.models import MovementType, StockMovement


class ReceiveError(ValueError):
    pass


def refresh_requisition_status(requisition: PurchaseRequisition) -> None:
    lines = list(requisition.lines.only("quantity_required", "quantity_received"))
    if not lines:
        return
    if all(line.is_fully_received for line in lines):
        if requisition.status != RequisitionStatus.RECEIVED:
            requisition.status = RequisitionStatus.RECEIVED
            requisition.save(update_fields=["status"])
    elif any(line.quantity_received > 0 for line in lines):
        if requisition.status in (RequisitionStatus.PENDING_APPROVAL, RequisitionStatus.APPROVED):
            requisition.status = RequisitionStatus.ORDERED
            requisition.save(update_fields=["status"])


def maybe_advance_order_after_receipt(order: Order) -> bool:
    if order.status != OrderStatus.PURCHASING:
        return False
    if build_order_plan(order).shortage:
        return False
    order.status = OrderStatus.PRODUCTION
    order.save(update_fields=["status", "updated_at"])
    return True


def _receive_line_unlocked(
    line: PurchaseRequisitionLine,
    quantity: Decimal,
    *,
    location_id: int | None,
    user,
    note: str,
) -> StockMovement:
    if quantity <= 0:
        raise ReceiveError("Укажите количество больше нуля.")
    remaining = line.quantity_remaining
    if remaining <= 0:
        raise ReceiveError(f"По материалу «{line.material.name}» всё уже принято.")
    if quantity > remaining:
        raise ReceiveError(
            f"По «{line.material.name}» осталось принять не больше {remaining} "
            f"{line.material.get_unit_display()}."
        )

    req = line.requisition
    movement = StockMovement.objects.create(
        material_id=line.material_id,
        location_id=location_id,
        quantity=quantity,
        movement_type=MovementType.RECEIPT,
        reference_order_id=req.order_id,
        purchase_requisition_id=req.pk,
        requisition_line_id=line.pk,
        note=note or f"Приход по заявке №{req.pk}",
        created_by=user,
    )
    line.quantity_received += quantity
    line.save(update_fields=["quantity_received"])
    return movement


@transaction.atomic
def receive_requisition_line(
    line: PurchaseRequisitionLine,
    quantity: Decimal,
    *,
    location_id: int | None = None,
    user=None,
    note: str = "",
) -> StockMovement:
    line = PurchaseRequisitionLine.objects.select_for_update().select_related("material", "requisition").get(
        pk=line.pk
    )
    movement = _receive_line_unlocked(line, quantity, location_id=location_id, user=user, note=note)
    refresh_requisition_status(line.requisition)
    if line.requisition.order_id:
        maybe_advance_order_after_receipt(
            Order.objects.select_for_update().get(pk=line.requisition.order_id)
        )
    return movement


@transaction.atomic
def receive_requisition_bulk(
    requisition: PurchaseRequisition,
    quantities: dict[int, Decimal],
    *,
    location_id: int | None = None,
    user=None,
) -> list[StockMovement]:
    requisition = PurchaseRequisition.objects.select_for_update().get(pk=requisition.pk)
    line_map = {
        ln.pk: ln
        for ln in requisition.lines.select_for_update().select_related("material")
    }
    movements: list[StockMovement] = []
    for line_id, qty in quantities.items():
        if qty <= 0:
            continue
        line = line_map.get(line_id)
        if line is None:
            raise ReceiveError("Неверная строка заявки.")
        movements.append(_receive_line_unlocked(line, qty, location_id=location_id, user=user, note=""))

    refresh_requisition_status(requisition)
    if requisition.order_id:
        maybe_advance_order_after_receipt(
            Order.objects.select_for_update().get(pk=requisition.order_id)
        )
    return movements


def open_requisitions_queryset():
    return (
        PurchaseRequisition.objects.exclude(status=RequisitionStatus.RECEIVED)
        .select_related("order", "order__customer")
        .prefetch_related("lines__material")
        .order_by("-created_at")
    )
