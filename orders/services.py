from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from django.db import transaction

from orders.models import Order, OrderStatus
from orders.planning import build_order_plan, material_balances, material_requirements_for_order
from procurement.models import PurchaseRequisition, PurchaseRequisitionLine, RequisitionStatus
from warehouse.models import MovementType, StockMovement

# Re-export for backward compatibility
__all__ = [
    "ConfirmResult",
    "material_requirements_for_order",
    "material_balances",
    "shortage_for_order",
    "confirm_order_and_plan_procurement",
    "register_stock_movement",
    "issue_material_to_order",
    "receipt_material",
]


@dataclass
class ConfirmResult:
    order: Order
    requisition: PurchaseRequisition | None
    created_requisition: bool
    updated_requisition: bool


def shortage_for_order(order: Order) -> dict[int, Decimal]:
    return build_order_plan(order).shortage


def _open_requisition(order: Order) -> PurchaseRequisition | None:
    return (
        order.purchase_requisitions.exclude(status=RequisitionStatus.RECEIVED)
        .order_by("-pk")
        .first()
    )


def _sync_requisition_lines(req: PurchaseRequisition, shortage: dict[int, Decimal]) -> bool:
    """Обновить строки заявки под текущую нехватку. Возвращает True, если были изменения."""
    changed = False
    existing = {line.material_id: line for line in req.lines.select_for_update().select_related("material")}
    for mid, gap in shortage.items():
        if mid in existing:
            line = existing[mid]
            new_required = line.quantity_received + gap
            if line.quantity_required != new_required:
                line.quantity_required = new_required
                line.save(update_fields=["quantity_required"])
                changed = True
        else:
            PurchaseRequisitionLine.objects.create(
                requisition=req,
                material_id=mid,
                quantity_required=gap,
            )
            changed = True
    stale_ids = [mid for mid, line in existing.items() if mid not in shortage and line.quantity_received == 0]
    if stale_ids:
        PurchaseRequisitionLine.objects.filter(requisition=req, material_id__in=stale_ids).delete()
        changed = True
    return changed


@transaction.atomic
def confirm_order_and_plan_procurement(order: Order) -> ConfirmResult:
    """
    Расчёт потребности и заявка при нехватке.
    Повторный вызов обновляет открытую заявку, а не создаёт дубликат.
    """
    order = Order.objects.select_for_update().get(pk=order.pk)
    plan = build_order_plan(order)

    if not plan.need:
        order.status = OrderStatus.PRODUCTION
        order.save(update_fields=["status", "updated_at"])
        return ConfirmResult(order=order, requisition=None, created_requisition=False, updated_requisition=False)

    if not plan.shortage:
        order.status = OrderStatus.PRODUCTION
        order.save(update_fields=["status", "updated_at"])
        return ConfirmResult(order=order, requisition=None, created_requisition=False, updated_requisition=False)

    req = _open_requisition(order)
    created = False
    updated = False

    if req is None:
        req = PurchaseRequisition.objects.create(
            order=order,
            status=RequisitionStatus.PENDING_APPROVAL,
            title=f"Материалы под заказ #{order.pk}",
        )
        for mid, gap in plan.shortage.items():
            PurchaseRequisitionLine.objects.create(
                requisition=req,
                material_id=mid,
                quantity_required=gap,
            )
        created = True
    else:
        updated = _sync_requisition_lines(req, plan.shortage)

    order.status = OrderStatus.PURCHASING
    order.save(update_fields=["status", "updated_at"])
    return ConfirmResult(
        order=order,
        requisition=req,
        created_requisition=created,
        updated_requisition=updated,
    )


def register_stock_movement(
    *,
    material_id: int,
    quantity: Decimal,
    movement_type: str,
    location_id: int | None = None,
    order_id: int | None = None,
    note: str = "",
    user=None,
) -> StockMovement:
    return StockMovement.objects.create(
        material_id=material_id,
        location_id=location_id,
        quantity=quantity,
        movement_type=movement_type,
        reference_order_id=order_id,
        note=note,
        created_by=user,
    )


def issue_material_to_order(material_id: int, quantity: Decimal, order_id: int, user=None) -> StockMovement:
    if quantity <= 0:
        raise ValueError("quantity must be positive")
    return register_stock_movement(
        material_id=material_id,
        quantity=-quantity,
        movement_type=MovementType.ISSUE,
        order_id=order_id,
        user=user,
    )


def receipt_material(material_id: int, quantity: Decimal, location_id: int | None = None, user=None) -> StockMovement:
    if quantity <= 0:
        raise ValueError("quantity must be positive")
    return register_stock_movement(
        material_id=material_id,
        quantity=quantity,
        movement_type=MovementType.RECEIPT,
        location_id=location_id,
        user=user,
    )
