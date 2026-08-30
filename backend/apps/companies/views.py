from django.db.models import Q
from rest_framework import permissions, status, viewsets
from apps.subscriptions.permissions import HasActiveSubscription
from rest_framework.response import Response

from .models import SellerProfile
from .serializers import SellerProfileSerializer


class SellerProfileViewSet(viewsets.ModelViewSet):
    permission_classes = (permissions.IsAuthenticated, HasActiveSubscription)
    serializer_class = SellerProfileSerializer

    def get_queryset(self):
        queryset = SellerProfile.objects.filter(owner=self.request.user, is_active=True)
        search = self.request.query_params.get("search", "").strip()
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search)
                | Q(phone_number__icontains=search)
                | Q(economic_code__icontains=search)
                | Q(national_id__icontains=search)
            )
        return queryset

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)

    def destroy(self, request, *args, **kwargs):
        profile = self.get_object()
        profile.is_active = False
        profile.save(update_fields=("is_active", "updated_at"))
        return Response(status=status.HTTP_204_NO_CONTENT)
