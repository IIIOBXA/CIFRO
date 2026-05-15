from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import TYPE_CHECKING

from django.db.models import Sum

from catalog.models import BillOfMaterialLine, Material
from warehouse.models import StockMovement

if TYPE_CHECKING:
    from orders.models import Order


@dataclass(frozen=True)
class MaterialPlanRow:
    material: Material
    required: Decimal
    on_hand: Decimal

    @property
    def shortage(self) -> Decimal:
        gap = self.required - self.on_hand
        return gap if gap > 0 else Decimal("0")


@dataclass(frozen=True)
class OrderPlan:
    need: dict[int, Decimal]
    balances: dict[int, Decimal]
    shortage: dict[int, Decimal]

    def material_ids(self) -> list[int]:
        return list(self.need.keys())

    def rows(self) -> list[MaterialPlanRow]:
        if not self.need:
            return []
        materials = Material.objects.in_bulk(self.need.keys())
        return [
            MaterialPlanRow(
                material=materials[mid],
                required=self.need[mid],
                on_hand=self.balances.get(mid, Decimal("0")),
            )
            for mid in self.need
            if mid in materials
        ]

    def shortage_rows(self) -> list[MaterialPlanRow]:
        return [row for row in self.rows() if row.shortage > 0]


def material_requirements_for_order(order: Order) -> dict[int, Decimal]:
    needed: dict[int, Decimal] = {}
    lines = BillOfMaterialLine.objects.filter(product_id=order.product_template_id).only(
        "material_id", "quantity_per_unit"
    )
    qty = Decimal(order.quantity)
    for line in lines:
        mid = line.material_id
        needed[mid] = needed.get(mid, Decimal("0")) + line.quantity_per_unit * qty
    return needed


def material_balances(material_ids: list[int] | None = None) -> dict[int, Decimal]:
    qs = StockMovement.objects.values("material_id").annotate(total=Sum("quantity")).order_by()
    if material_ids is not None:
        qs = qs.filter(material_id__in=material_ids)
    return {row["material_id"]: row["total"] or Decimal("0") for row in qs}


def build_order_plan(order: Order) -> OrderPlan:
    need = material_requirements_for_order(order)
    balances = material_balances(list(need.keys())) if need else {}
    shortage = {
        mid: need[mid] - balances.get(mid, Decimal("0"))
        for mid in need
        if need[mid] > balances.get(mid, Decimal("0"))
    }
    return OrderPlan(need=need, balances=balances, shortage=shortage)
