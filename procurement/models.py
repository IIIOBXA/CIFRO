from decimal import Decimal

from django.core.validators import MinValueValidator
from django.db import models


class RequisitionStatus(models.TextChoices):
    DRAFT = "draft", "Черновик"
    PENDING_APPROVAL = "pending_approval", "На согласовании"
    APPROVED = "approved", "Утверждена"
    ORDERED = "ordered", "Заказана у поставщика"
    RECEIVED = "received", "Получена"


class Supplier(models.Model):
    name = models.CharField("Название", max_length=255)
    contact_person = models.CharField("Контакт", max_length=255, blank=True)
    phone = models.CharField("Телефон", max_length=32, blank=True)
    email = models.EmailField("E-mail", blank=True)
    lead_time_days = models.PositiveIntegerField("Срок поставки, дн.", default=7)
    notes = models.TextField("Заметки", blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Поставщик"
        verbose_name_plural = "Поставщики"
        ordering = ["name"]

    def __str__(self) -> str:
        return self.name


class PurchaseRequisition(models.Model):
    """Заявка на закупку (может быть привязана к заказу)."""

    order = models.ForeignKey(
        "orders.Order",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="purchase_requisitions",
        verbose_name="Заказ",
    )
    status = models.CharField(
        "Статус",
        max_length=32,
        choices=RequisitionStatus.choices,
        default=RequisitionStatus.PENDING_APPROVAL,
    )
    title = models.CharField("Название", max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    approved_at = models.DateTimeField(null=True, blank=True)
    approved_by = models.ForeignKey(
        "auth.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="approved_requisitions",
    )

    class Meta:
        verbose_name = "Заявка на закупку"
        verbose_name_plural = "Заявки на закупку"
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return self.title or f"Заявка #{self.pk}"


class PurchaseRequisitionLine(models.Model):
    requisition = models.ForeignKey(
        PurchaseRequisition,
        on_delete=models.CASCADE,
        related_name="lines",
        verbose_name="Заявка",
    )
    material = models.ForeignKey(
        "catalog.Material",
        on_delete=models.PROTECT,
        related_name="purchase_lines",
        verbose_name="Материал",
    )
    quantity_required = models.DecimalField(
        "Требуется закупить",
        max_digits=14,
        decimal_places=4,
        validators=[MinValueValidator(Decimal("0.0001"))],
    )
    suggested_supplier = models.ForeignKey(
        Supplier,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Поставщик",
    )
    unit_price_estimate = models.DecimalField(
        "Оценка цены за ед.",
        max_digits=14,
        decimal_places=2,
        null=True,
        blank=True,
    )
    quantity_received = models.DecimalField(
        "Уже принято на склад",
        max_digits=14,
        decimal_places=4,
        default=Decimal("0"),
        validators=[MinValueValidator(Decimal("0"))],
    )

    class Meta:
        verbose_name = "Строка заявки"
        verbose_name_plural = "Строки заявок"

    def __str__(self) -> str:
        return f"{self.material.sku} × {self.quantity_required}"

    @property
    def quantity_remaining(self) -> Decimal:
        left = self.quantity_required - self.quantity_received
        return left if left > 0 else Decimal("0")

    @property
    def is_fully_received(self) -> bool:
        return self.quantity_received >= self.quantity_required
