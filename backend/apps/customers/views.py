from django.db.models import Q
from rest_framework import permissions, viewsets
from rest_framework.response import Response

from .models import Customer
from .serializers import CustomerSerializer


class CustomerViewSet(viewsets.ModelViewSet):
    permission_classes = (permissions.IsAuthenticated,)
    serializer_class = CustomerSerializer

    def get_queryset(self):
        queryset = Customer.objects.filter(owner=self.request.user, is_active=True)
        search = self.request.query_params.get("search", "").strip()
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search)
                | Q(company_name__icontains=search)
                | Q(phone_number__icontains=search)
            )
        return queryset

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)

    def destroy(self, request, *args, **kwargs):
        customer = self.get_object()
        customer.is_active = False
        customer.save(update_fields=("is_active", "updated_at"))
        return Response(status=204)
