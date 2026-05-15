from decimal import Decimal

from django.core.validators import MinValueValidator
from django.db import models


class Unit(models.TextChoices):
    PCS = "pcs", "шт."
    M = "m", "м"
    M2 = "m2", "м²"
    M3 = "m3", "м³"
    KG = "kg", "кг"
    SHEET = "sheet", "лист"
    SET = "set", "комплект"


class Material(models.Model):
    """Материал / номенклатура для склада и спецификаций."""

    sku = models.CharField("Код (SKU)", max_length=64, unique=True, db_index=True)
    name = models.CharField("Наименование", max_length=255)
    unit = models.CharField("Ед. изм.", max_length=16, choices=Unit.choices, default=Unit.PCS)
    min_quantity = models.DecimalField(
        "Минимальный остаток",
        max_digits=14,
        decimal_places=4,
        default=Decimal("0"),
        validators=[MinValueValidator(Decimal("0"))],
    )
    storage_hint = models.CharField(
        "Подсказка по размещению (текст)",
        max_length=255,
        blank=True,
        help_text="Позже можно связать с ячейкой склада через движения.",
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Материал"
        verbose_name_plural = "Материалы"
        ordering = ["sku"]

    def __str__(self) -> str:
        return f"{self.sku} — {self.name}"


class ProductTemplate(models.Model):
    """Шаблон изделия (кухня, шкаф и т.д.) с привязкой к спецификации."""

    code = models.SlugField("Код", max_length=64, unique=True)
    name = models.CharField("Название", max_length=255)
    description = models.TextField("Описание", blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Шаблон изделия"
        verbose_name_plural = "Шаблоны изделий"
        ordering = ["name"]

    def __str__(self) -> str:
        return self.name


class BillOfMaterialLine(models.Model):
    """Строка спецификации: материал на единицу изделия."""

    product = models.ForeignKey(
        ProductTemplate,
        on_delete=models.CASCADE,
        related_name="bom_lines",
        verbose_name="Изделие",
    )
    material = models.ForeignKey(
        Material,
        on_delete=models.PROTECT,
        related_name="bom_usages",
        verbose_name="Материал",
    )
    quantity_per_unit = models.DecimalField(
        "Кол-во на 1 изделие",
        max_digits=14,
        decimal_places=4,
        validators=[MinValueValidator(Decimal("0.0001"))],
    )

    class Meta:
        verbose_name = "Строка спецификации"
        verbose_name_plural = "Спецификации (BOM)"
        unique_together = [("product", "material")]

    def __str__(self) -> str:
        return f"{self.product} → {self.material.sku} × {self.quantity_per_unit}"
