from decimal import Decimal

from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models


class OrderStatus(models.TextChoices):
    NEW = "new", "Новый"
    CALCULATING = "calculating", "В расчёте"
    PRODUCTION = "production", "В производстве"
    AT_WAREHOUSE = "at_warehouse", "На складе (готовая продукция)"
    PURCHASING = "purchasing", "В закупке (материалы)"
    READY = "ready", "Готов к отгрузке"
    SHIPPED = "shipped", "Отгружен"


class Order(models.Model):
    customer = models.ForeignKey(
        "customers.Customer",
        on_delete=models.PROTECT,
        related_name="orders",
        verbose_name="Клиент",
    )
    product_template = models.ForeignKey(
        "catalog.ProductTemplate",
        on_delete=models.PROTECT,
        related_name="orders",
        verbose_name="Изделие (шаблон)",
    )
    quantity = models.PositiveIntegerField(
        "Количество изделий",
        default=1,
        validators=[MinValueValidator(1)],
    )
    status = models.CharField(
        "Статус",
        max_length=32,
        choices=OrderStatus.choices,
        default=OrderStatus.NEW,
        db_index=True,
    )
    notes = models.TextField("Примечания", blank=True)
    internal_number = models.CharField("Внутренний номер", max_length=64, blank=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="orders_created",
    )

    class Meta:
        verbose_name = "Заказ"
        verbose_name_plural = "Заказы"
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"Заказ #{self.pk} — {self.customer}"
