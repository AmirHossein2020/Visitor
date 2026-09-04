from django.db.models import Q
from rest_framework import permissions, status, viewsets
from apps.subscriptions.permissions import HasActiveSubscription
from rest_framework.response import Response
from rest_framework.decorators import action
from django.http import FileResponse
from pathlib import Path

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

    def _asset_response(self, profile, field_name):
        asset = getattr(profile, field_name)
        if not asset:
            return Response({"detail": "تصویری ثبت نشده است."}, status=404)
        suffix = Path(asset.name).suffix.lower()
        content_type = {".png":"image/png", ".jpg":"image/jpeg", ".jpeg":"image/jpeg", ".webp":"image/webp"}.get(suffix, "application/octet-stream")
        return FileResponse(asset.open("rb"), content_type=content_type)

    def _remove_asset(self, profile, field_name):
        asset = getattr(profile, field_name)
        if asset:
            asset.delete(save=False)
            setattr(profile, field_name, "")
            profile.save(update_fields=(field_name, "updated_at"))
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=("get", "delete"), url_path="stamp")
    def stamp(self, request, pk=None):
        profile = self.get_object()
        return self._remove_asset(profile, "stamp_image") if request.method == "DELETE" else self._asset_response(profile, "stamp_image")

    @action(detail=True, methods=("get", "delete"), url_path="signature")
    def signature(self, request, pk=None):
        profile = self.get_object()
        return self._remove_asset(profile, "signature_image") if request.method == "DELETE" else self._asset_response(profile, "signature_image")
