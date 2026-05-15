import pytest
from decimal import Decimal

from catalog.models import BillOfMaterialLine, Material, ProductTemplate, Unit
from customers.models import Customer
from orders.models import Order, OrderStatus
from orders.services import confirm_order_and_plan_procurement
from procurement.models import RequisitionStatus
from procurement.services import receive_requisition_line
from django.db.models import Sum

from warehouse.models import StockMovement


@pytest.mark.django_db
def test_receive_updates_stock_and_closes_requisition():
    m = Material.objects.create(sku="R1", name="Доска", unit=Unit.PCS)
    p = ProductTemplate.objects.create(code="r1", name="Шкаф")
    BillOfMaterialLine.objects.create(product=p, material=m, quantity_per_unit=Decimal("10"))
    c = Customer.objects.create(name="Клиент", phone="+71111111111")
    order = Order.objects.create(customer=c, product_template=p, quantity=1)
    result = confirm_order_and_plan_procurement(order)
    assert result.requisition is not None
    line = result.requisition.lines.get()

    receive_requisition_line(line, Decimal("10"), user=None)

    line.refresh_from_db()
    assert line.quantity_received == Decimal("10")
    assert line.is_fully_received
    result.requisition.refresh_from_db()
    assert result.requisition.status == RequisitionStatus.RECEIVED
    bal = StockMovement.objects.filter(material=m).aggregate(total=Sum("quantity"))["total"]
    assert bal == Decimal("10")

    order.refresh_from_db()
    assert order.status == OrderStatus.PRODUCTION


@pytest.mark.django_db
def test_partial_receive_keeps_requisition_open():
    m = Material.objects.create(sku="R2", name="Кромка", unit=Unit.M)
    p = ProductTemplate.objects.create(code="r2", name="Кухня")
    BillOfMaterialLine.objects.create(product=p, material=m, quantity_per_unit=Decimal("5"))
    c = Customer.objects.create(name="К2", phone="+72222222222")
    order = Order.objects.create(customer=c, product_template=p, quantity=1)
    result = confirm_order_and_plan_procurement(order)
    line = result.requisition.lines.get()

    receive_requisition_line(line, Decimal("2"))

    line.refresh_from_db()
    assert line.quantity_remaining == Decimal("3")
    result.requisition.refresh_from_db()
    assert result.requisition.status == RequisitionStatus.ORDERED
