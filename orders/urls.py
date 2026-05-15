from django.urls import path

from orders import web_views

urlpatterns = [
    path("", web_views.dashboard, name="dashboard"),
    path("help/", web_views.help_page, name="help"),
    path("orders/", web_views.order_list, name="order-list"),
    path("orders/create/", web_views.order_create, name="order-create"),
    path("orders/<int:pk>/", web_views.order_detail, name="order-detail"),
    path("orders/<int:pk>/confirm/", web_views.order_confirm, name="order-confirm"),
    path("clients/", web_views.customer_list, name="customer-list"),
]
