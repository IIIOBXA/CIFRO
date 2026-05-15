from django.urls import path

from warehouse import web_views

urlpatterns = [
    path("warehouse/", web_views.requisition_list, name="warehouse-requisition-list"),
    path(
        "warehouse/requisitions/<int:pk>/receive/",
        web_views.requisition_receive,
        name="warehouse-requisition-receive",
    ),
]
