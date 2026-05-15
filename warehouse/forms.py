from decimal import Decimal

from django import forms

from warehouse.models import StorageLocation


class ReceiveRequisitionForm(forms.Form):
    """Общая ячейка для всей поставки (необязательно)."""

    location = forms.ModelChoiceField(
        label="Куда положить (ячейка склада)",
        queryset=StorageLocation.objects.filter(is_active=True),
        required=False,
        empty_label="— не указывать —",
        help_text="Можно выбрать стеллаж/полку, куда положили материал.",
    )

    def __init__(self, requisition, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.requisition = requisition
        for line in requisition.lines.select_related("material").order_by("pk"):
            if line.quantity_remaining <= 0:
                continue
            self.fields[f"qty_{line.pk}"] = forms.DecimalField(
                label=line.material.name,
                min_value=Decimal("0"),
                max_value=line.quantity_remaining,
                required=False,
                initial=line.quantity_remaining,
                decimal_places=4,
                help_text=(
                    f"Заказано: {line.quantity_required} {line.material.get_unit_display()}. "
                    f"Уже на складе по этой заявке: {line.quantity_received}. "
                    f"Осталось принять: {line.quantity_remaining}."
                ),
                widget=forms.NumberInput(attrs={"step": "0.0001", "min": "0"}),
            )

    def line_quantities(self) -> dict[int, Decimal]:
        result: dict[int, Decimal] = {}
        for name, value in self.cleaned_data.items():
            if not name.startswith("qty_") or value is None:
                continue
            if value > 0:
                result[int(name.removeprefix("qty_"))] = value
        return result
