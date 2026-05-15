from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404, redirect, render

from customers.models import Customer
from orders.forms import OrderForm
from orders.models import Order, OrderStatus
from orders.planning import build_order_plan
from orders.services import ConfirmResult, confirm_order_and_plan_procurement
from procurement.models import RequisitionStatus
from procurement.services import open_requisitions_queryset


def _order_detail_context(order: Order) -> dict:
    plan = build_order_plan(order)
    requisitions = order.purchase_requisitions.prefetch_related("lines__material").all()
    can_confirm = order.status in (OrderStatus.NEW, OrderStatus.CALCULATING, OrderStatus.PURCHASING)
    return {
        "order": order,
        "plan": plan,
        "requisitions": requisitions,
        "show_calculate_button": can_confirm,
    }


@login_required
def dashboard(request):
    open_reqs = open_requisitions_queryset()
    return render(
        request,
        "dashboard.html",
        {
            "orders_count": Order.objects.count(),
            "customers_count": Customer.objects.filter(is_active=True).count(),
            "recent_orders": Order.objects.select_related("customer", "product_template")[:8],
            "new_orders_count": Order.objects.filter(status=OrderStatus.NEW).count(),
            "open_requisitions_count": open_reqs.count(),
            "open_requisitions": open_reqs[:5],
        },
    )


@login_required
def order_list(request):
    orders = (
        Order.objects.select_related("customer", "product_template")
        .annotate(req_count=Count("purchase_requisitions", filter=~Q(purchase_requisitions__status=RequisitionStatus.RECEIVED)))
        .order_by("-created_at")
    )
    return render(request, "orders/order_list.html", {"orders": orders})


@login_required
def order_create(request):
    form = OrderForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        order = form.save(commit=False)
        order.created_by = request.user
        order.save()
        messages.success(
            request,
            f"Заказ № {order.pk} сохранён. Откройте его и нажмите «Посчитать материалы».",
        )
        return redirect("order-detail", pk=order.pk)
    return render(request, "orders/order_form.html", {"form": form, "title": "Новый заказ от клиента"})


@login_required
def order_detail(request, pk: int):
    order = get_object_or_404(
        Order.objects.select_related("customer", "product_template"),
        pk=pk,
    )
    return render(request, "orders/order_detail.html", _order_detail_context(order))


@login_required
def order_confirm(request, pk: int):
    if request.method != "POST":
        return redirect("order-detail", pk=pk)
    order = get_object_or_404(Order, pk=pk)
    result: ConfirmResult = confirm_order_and_plan_procurement(order)
    if result.requisition is None:
        messages.success(
            request,
            "Готово: все материалы на складе. Заказ переведён в этап «В производстве».",
        )
    elif result.created_requisition:
        messages.success(
            request,
            "Создана заявка на закупку — не хватает материалов. После поставки примите их в разделе «Приём на склад».",
        )
    elif result.updated_requisition:
        messages.success(request, "Заявка на закупку обновлена по текущим остаткам склада.")
    else:
        messages.info(request, "Расчёт выполнен. Заявка на закупку уже была открыта.")
    return redirect("order-detail", pk=pk)


@login_required
def customer_list(request):
    customers = Customer.objects.filter(is_active=True).order_by("organization", "name")
    return render(request, "customers/customer_list.html", {"customers": customers})


@login_required
def help_page(request):
    return render(request, "help.html")
