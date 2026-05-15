from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets

from customers.models import Customer
from customers.serializers import CustomerSerializer


class CustomerViewSet(viewsets.ModelViewSet):
    queryset = Customer.objects.all()
    serializer_class = CustomerSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["is_active", "payment_status"]
    search_fields = ["name", "organization", "phone", "email"]
