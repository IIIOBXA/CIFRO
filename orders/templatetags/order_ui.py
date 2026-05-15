from django import template

register = template.Library()

STATUS_HINTS = {
    "new": "Заказ записан в программу. Дальше нужно нажать кнопку «Посчитать материалы».",
    "calculating": "Идёт подсчёт, что нужно купить и взять со склада.",
    "production": "Материалы есть — можно делать мебель в цехе.",
    "at_warehouse": "Изделие лежит на складе, ждёт отгрузки клиенту.",
    "purchasing": "Не хватает материалов — оформлена заявка на закупку.",
    "ready": "Всё готово, можно отдавать клиенту.",
    "shipped": "Заказ отдан клиенту, работа по нему завершена.",
}

STATUS_CSS = {
    "new": "status-new",
    "calculating": "status-work",
    "production": "status-work",
    "at_warehouse": "status-work",
    "purchasing": "status-warn",
    "ready": "status-ok",
    "shipped": "status-done",
}


@register.filter
def status_hint(status_code: str) -> str:
    return STATUS_HINTS.get(status_code, "")


@register.filter
def status_css(status_code: str) -> str:
    return STATUS_CSS.get(status_code, "status-new")


@register.filter
def can_calculate_materials(status_code: str) -> bool:
    return status_code in ("new", "calculating")
