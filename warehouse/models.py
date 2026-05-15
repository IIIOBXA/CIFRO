from decimal import Decimal

from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models


class StorageLocation(models.Model):
    """Адрес хранения: стеллаж / полка / ячейка."""

    code = models.CharField("Код ячейки", max_length=64, unique=True, db_index=True)
    description = models.CharField("Описание", max_length=255, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Ячейка склада"
        verbose_name_plural = "Ячейки склада"
        ordering = ["code"]

    def __str__(self) -> str:
        return self.code


class MovementType(models.TextChoices):
    RECEIPT = "receipt", "Приход"
    ISSUE = "issue", "Расход"
    TRANSFER_OUT = "transfer_out", "Перемещение (отправка)"
    TRANSFER_IN = "transfer_in", "Перемещение (приём)"
    RESERVE = "reserve", "Резерв"
    RESERVE_RELEASE = "reserve_release", "Снятие резерва"
    WRITEOFF = "writeoff", "Списание"
    INVENTORY = "inventory", "Инвентаризация"


class StockMovement(models.Model):
    """
    Движение по складу: количество со знаком.
    Положительное — приход, отрицательное — расход/списание.
    """

    material = models.ForeignKey(
        "catalog.Material",
        on_delete=models.PROTECT,
        related_name="movements",
        verbose_name="Материал",
    )
    location = models.ForeignKey(
        StorageLocation,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="movements",
        verbose_name="Ячейка",
    )
    quantity = models.DecimalField(
        "Количество (+ приход / − расход)",
        max_digits=14,
        decimal_places=4,
    )
    movement_type = models.CharField(
        "Тип операции",
        max_length=32,
        choices=MovementType.choices,
    )
    reference_order = models.ForeignKey(
        "orders.Order",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="stock_movements",
        verbose_name="Заказ",
    )
    purchase_requisition = models.ForeignKey(
        "procurement.PurchaseRequisition",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="stock_movements",
        verbose_name="Заявка на закупку",
    )
    requisition_line = models.ForeignKey(
        "procurement.PurchaseRequisitionLine",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="stock_movements",
        verbose_name="Строка заявки",
    )
    note = models.CharField("Комментарий", max_length=500, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="stock_movements_created",
    )

    class Meta:
        verbose_name = "Движение склада"
        verbose_name_plural = "Движения склада"
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"{self.get_movement_type_display()} {self.material_id} {self.quantity}"
