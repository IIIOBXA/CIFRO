import pytest
from decimal import Decimal

from catalog.models import BillOfMaterialLine, Material, ProductTemplate, Unit
from customers.models import Customer
from orders.models import Order, OrderStatus
from orders.services import confirm_order_and_plan_procurement
from procurement.models import PurchaseRequisition, RequisitionStatus
from warehouse.models import MovementType, StockMovement


@pytest.mark.django_db
def test_material_requirements_multiplies_bom_by_quantity():
    from orders.planning import material_requirements_for_order

    m = Material.objects.create(sku="T1", name="Test", unit=Unit.PCS)
    p = ProductTemplate.objects.create(code="p1", name="Product 1")
    BillOfMaterialLine.objects.create(product=p, material=m, quantity_per_unit=Decimal("2.5"))
    c = Customer.objects.create(name="C", phone="+70000000001")
    order = Order.objects.create(customer=c, product_template=p, quantity=3)
    need = material_requirements_for_order(order)
    assert need[m.id] == Decimal("7.5")


@pytest.mark.django_db
def test_shortage_when_stock_insufficient():
    from orders.planning import build_order_plan

    m = Material.objects.create(sku="T2", name="Test2", unit=Unit.PCS)
    p = ProductTemplate.objects.create(code="p2", name="Product 2")
    BillOfMaterialLine.objects.create(product=p, material=m, quantity_per_unit=Decimal("10"))
    c = Customer.objects.create(name="C2", phone="+70000000002")
    order = Order.objects.create(customer=c, product_template=p, quantity=1)
    StockMovement.objects.create(material=m, quantity=Decimal("3"), movement_type=MovementType.RECEIPT)
    assert build_order_plan(order).shortage[m.id] == Decimal("7")


@pytest.mark.django_db
def test_confirm_creates_requisition_when_shortage():
    m = Material.objects.create(sku="T3", name="Test3", unit=Unit.PCS)
    p = ProductTemplate.objects.create(code="p3", name="Product 3")
    BillOfMaterialLine.objects.create(product=p, material=m, quantity_per_unit=Decimal("5"))
    c = Customer.objects.create(name="C3", phone="+70000000003")
    order = Order.objects.create(customer=c, product_template=p, quantity=1)
    result = confirm_order_and_plan_procurement(order)
    assert result.requisition is not None
    assert result.created_requisition
    assert result.order.status == OrderStatus.PURCHASING


@pytest.mark.django_db
def test_confirm_goes_production_when_enough_stock():
    m = Material.objects.create(sku="T4", name="Test4", unit=Unit.PCS)
    p = ProductTemplate.objects.create(code="p4", name="Product 4")
    BillOfMaterialLine.objects.create(product=p, material=m, quantity_per_unit=Decimal("2"))
    c = Customer.objects.create(name="C4", phone="+70000000004")
    order = Order.objects.create(customer=c, product_template=p, quantity=1)
    StockMovement.objects.create(material=m, quantity=Decimal("100"), movement_type=MovementType.RECEIPT)
    result = confirm_order_and_plan_procurement(order)
    assert result.requisition is None
    assert result.order.status == OrderStatus.PRODUCTION


@pytest.mark.django_db
def test_confirm_does_not_duplicate_requisition():
    m = Material.objects.create(sku="T5", name="Test5", unit=Unit.PCS)
    p = ProductTemplate.objects.create(code="p5", name="Product 5")
    BillOfMaterialLine.objects.create(product=p, material=m, quantity_per_unit=Decimal("5"))
    c = Customer.objects.create(name="C5", phone="+70000000005")
    order = Order.objects.create(customer=c, product_template=p, quantity=1)
    r1 = confirm_order_and_plan_procurement(order)
    r2 = confirm_order_and_plan_procurement(order)
    assert PurchaseRequisition.objects.filter(order=order).count() == 1
    assert r2.requisition.pk == r1.requisition.pk
    assert r2.created_requisition is False
