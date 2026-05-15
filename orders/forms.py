from django import forms

from orders.models import Order, OrderStatus


class OrderForm(forms.ModelForm):
    """Форма для менеджера: только то, что нужно при приёме заказа."""

    class Meta:
        model = Order
        fields = ["customer", "product_template", "quantity", "notes", "internal_number"]
        labels = {
            "customer": "Кто заказал (клиент)",
            "product_template": "Что делаем (тип мебели)",
            "quantity": "Сколько штук",
            "notes": "Заметки для себя",
            "internal_number": "Номер заказа в вашей бумажной записи (необязательно)",
        }
        help_texts = {
            "customer": "Выберите клиента из списка. Если его нет — попросите администратора добавить в разделе «Справочники».",
            "product_template": "Например: кухня, шкаф. Программа сама посчитает, сколько материалов нужно.",
            "quantity": "Сколько таких изделий нужно сделать по этому заказу.",
            "notes": "Например: цвет фасада, срок, особые пожелания клиента.",
            "internal_number": "Можно оставить пустым — тогда будет только номер в программе.",
        }
        widgets = {
            "quantity": forms.NumberInput(attrs={"min": 1, "step": 1}),
            "notes": forms.Textarea(attrs={"rows": 3, "placeholder": "Напишите здесь всё важное по заказу"}),
            "internal_number": forms.TextInput(attrs={"placeholder": "Например: 15/05-Иванов"}),
        }

    def save(self, commit=True):
        instance = super().save(commit=False)
        if not instance.pk:
            instance.status = OrderStatus.NEW
        if commit:
            instance.save()
        return instance
