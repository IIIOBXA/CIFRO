from decimal import Decimal

from django.core.management.base import BaseCommand, CommandError

from catalog.models import Material, Unit


class Command(BaseCommand):
    help = "Импорт материалов из Excel (.xlsx). Колонки: sku, name, unit, min_quantity (опционально)."

    def add_arguments(self, parser):
        parser.add_argument("path", type=str)

    def handle(self, *args, **options):
        path = options["path"]
        try:
            import pandas as pd
        except ImportError as e:
            raise CommandError("Нужен pandas: pip install pandas openpyxl") from e

        df = pd.read_excel(path)
        df.columns = [str(c).strip().lower() for c in df.columns]
        required = {"sku", "name", "unit"}
        cols = set(df.columns)
        if not required.issubset(cols):
            raise CommandError(f"В файле должны быть колонки {required}, сейчас: {df.columns.tolist()}")

        created = 0
        for _, row in df.iterrows():
            sku = str(row["sku"]).strip()
            name = str(row["name"]).strip()
            unit_raw = str(row["unit"]).strip().lower()
            unit_map = {u.value: u.value for u in Unit}
            unit_map.update({"шт": Unit.PCS, "шт.": Unit.PCS, "м2": Unit.M2, "м": Unit.M})
            unit = unit_map.get(unit_raw, Unit.PCS)
            min_q = Decimal(str(row["min_quantity"])) if "min_quantity" in df.columns and pd.notna(row.get("min_quantity")) else Decimal("0")
            _, was_created = Material.objects.update_or_create(
                sku=sku,
                defaults={"name": name, "unit": unit, "min_quantity": min_q},
            )
            if was_created:
                created += 1
        self.stdout.write(self.style.SUCCESS(f"Готово. Новых записей: {created}, всего строк: {len(df)}"))
