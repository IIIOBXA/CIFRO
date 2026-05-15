from django.db import models


class PaymentStatus(models.TextChoices):
    UNKNOWN = "unknown", "Не указан"
    PENDING = "pending", "Ожидает оплаты"
    PARTIAL = "partial", "Частично оплачен"
    PAID = "paid", "Оплачен"


class Customer(models.Model):
    """Единый справочник клиентов — один ID на контрагента."""

    name = models.CharField("Имя / контактное лицо", max_length=255)
    organization = models.CharField("Организация", max_length=255, blank=True)
    phone = models.CharField("Телефон", max_length=32, unique=True)
    email = models.EmailField("E-mail", blank=True)
    address = models.TextField("Адрес", blank=True)
    requisites = models.TextField("Реквизиты", blank=True)
    manager_notes = models.TextField("Комментарии менеджера", blank=True)
    preferences = models.TextField("Предпочтения клиента", blank=True)
    payment_status = models.CharField(
        "Статус оплаты",
        max_length=20,
        choices=PaymentStatus.choices,
        default=PaymentStatus.UNKNOWN,
    )
    is_active = models.BooleanField("Активен", default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Клиент"
        verbose_name_plural = "Клиенты"
        ordering = ["organization", "name"]

    def __str__(self) -> str:
        if self.organization:
            return f"{self.organization} ({self.name})"
        return self.name
