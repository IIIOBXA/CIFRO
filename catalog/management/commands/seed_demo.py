from decimal import Decimal

from django.core.management.base import BaseCommand

from catalog.models import BillOfMaterialLine, Material, ProductTemplate, Unit
from customers.models import Customer, PaymentStatus
from orders.models import Order, OrderStatus
from warehouse.models import MovementType, StockMovement
from warehouse.models import StorageLocation


class Command(BaseCommand):
    help = "Загрузить демо-данные: клиент, материалы, шаблон кухни, BOM, остатки, тестовый заказ."

    def handle(self, *args, **options):
        loc_a, _ = StorageLocation.objects.get_or_create(code="A-01-01", defaults={"description": "Стеллаж A"})
        loc_b, _ = StorageLocation.objects.get_or_create(code="B-02-01", defaults={"description": "Стеллаж B"})

        m_ldsp, _ = Material.objects.get_or_create(
            sku="LDSP-18-W",
            defaults={
                "name": "ЛДСП 18 мм белый",
                "unit": Unit.SHEET,
                "min_quantity": Decimal("5"),
                "storage_hint": str(loc_a.code),
            },
        )
        m_dsp, _ = Material.objects.get_or_create(
            sku="DSP-38-OAK",
            defaults={
                "name": "Столешница ДСП 38 мм дуб",
                "unit": Unit.M,
                "min_quantity": Decimal("2"),
                "storage_hint": str(loc_b.code),
            },
        )
        m_edge, _ = Material.objects.get_or_create(
            sku="EDGE-2-W",
            defaults={
                "name": "Кромка ПВХ 2×23 белая",
                "unit": Unit.M,
                "min_quantity": Decimal("50"),
            },
        )
        m_screw, _ = Material.objects.get_or_create(
            sku="SCR-CONF",
            defaults={
                "name": "Конфирмат 6.3×50",
                "unit": Unit.PCS,
                "min_quantity": Decimal("200"),
            },
        )

        kitchen, _ = ProductTemplate.objects.get_or_create(
            code="kitchen-basic",
            defaults={"name": "Кухня (базовый модуль)", "description": "Демо-шаблон для расчёта материалов"},
        )
        BillOfMaterialLine.objects.get_or_create(
            product=kitchen,
            material=m_ldsp,
            defaults={"quantity_per_unit": Decimal("2")},
        )
        BillOfMaterialLine.objects.get_or_create(
            product=kitchen,
            material=m_dsp,
            defaults={"quantity_per_unit": Decimal("3")},
        )
        BillOfMaterialLine.objects.get_or_create(
            product=kitchen,
            material=m_edge,
            defaults={"quantity_per_unit": Decimal("12")},
        )
        BillOfMaterialLine.objects.get_or_create(
            product=kitchen,
            material=m_screw,
            defaults={"quantity_per_unit": Decimal("40")},
        )

        cust, _ = Customer.objects.get_or_create(
            phone="+79990001122",
            defaults={
                "name": "Иван Петров",
                "organization": "ООО «Демо»",
                "email": "demo@example.com",
                "address": "Москва",
                "payment_status": PaymentStatus.PENDING,
            },
        )

        if not StockMovement.objects.filter(material=m_ldsp).exists():
            StockMovement.objects.create(
                material=m_ldsp,
                location=loc_a,
                quantity=Decimal("10"),
                movement_type=MovementType.RECEIPT,
                note="Демо-приход",
            )
        if not StockMovement.objects.filter(material=m_dsp).exists():
            StockMovement.objects.create(
                material=m_dsp,
                location=loc_b,
                quantity=Decimal("5"),
                movement_type=MovementType.RECEIPT,
                note="Демо-приход",
            )
        if not StockMovement.objects.filter(material=m_edge).exists():
            StockMovement.objects.create(
                material=m_edge,
                quantity=Decimal("100"),
                movement_type=MovementType.RECEIPT,
                note="Демо-приход",
            )
        if not StockMovement.objects.filter(material=m_screw).exists():
            StockMovement.objects.create(
                material=m_screw,
                quantity=Decimal("500"),
                movement_type=MovementType.RECEIPT,
                note="Демо-приход",
            )

        if not Order.objects.exists():
            Order.objects.create(
                customer=cust,
                product_template=kitchen,
                quantity=2,
                status=OrderStatus.NEW,
                internal_number="DEMO-001",
                notes="Демонстрационный заказ",
            )

        self.stdout.write(self.style.SUCCESS("Демо-данные загружены. Создайте суперпользователя: python manage.py createsuperuser"))
