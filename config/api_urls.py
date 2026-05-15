from django.urls import include, path
from rest_framework.routers import DefaultRouter

from catalog.views import BillOfMaterialLineViewSet, MaterialViewSet, ProductTemplateViewSet
from customers.views import CustomerViewSet
from orders.api_views import OrderViewSet
from procurement.views import (
    PurchaseRequisitionLineViewSet,
    PurchaseRequisitionViewSet,
    SupplierViewSet,
)
from warehouse import views as warehouse_views
from warehouse.views import StockMovementViewSet, StorageLocationViewSet

router = DefaultRouter()
router.register(r"customers", CustomerViewSet)
router.register(r"materials", MaterialViewSet)
router.register(r"product-templates", ProductTemplateViewSet)
router.register(r"bom-lines", BillOfMaterialLineViewSet)
router.register(r"storage-locations", StorageLocationViewSet)
router.register(r"stock-movements", StockMovementViewSet)
router.register(r"suppliers", SupplierViewSet)
router.register(r"purchase-requisitions", PurchaseRequisitionViewSet)
router.register(r"purchase-requisition-lines", PurchaseRequisitionLineViewSet)
router.register(r"orders", OrderViewSet)

urlpatterns = [
    path("", include(router.urls)),
    path("materials/<str:sku>/qr.png", warehouse_views.material_qr_png, name="material-qr"),
]
