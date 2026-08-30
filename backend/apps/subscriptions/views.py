from rest_framework import generics, permissions, viewsets
from rest_framework.response import Response

from .models import SubscriptionOrder, SubscriptionPlan
from .permissions import active_subscription_for
from .serializers import SubscriptionOrderSerializer, SubscriptionPlanSerializer, UserSubscriptionSerializer


class PlanListView(generics.ListAPIView):
    permission_classes = (permissions.AllowAny,)
    serializer_class = SubscriptionPlanSerializer
    queryset = SubscriptionPlan.objects.filter(is_active=True)


class MySubscriptionView(generics.GenericAPIView):
    permission_classes = (permissions.IsAuthenticated,)

    def get(self, request):
        effective = active_subscription_for(request.user)
        if effective is True:
            return Response({"is_active": True, "is_superuser": True, "subscription": None})
        latest = request.user.subscriptions.select_related("plan").first()
        return Response({"is_active": bool(effective), "is_superuser": False, "subscription": UserSubscriptionSerializer(latest).data if latest else None})


class SubscriptionOrderViewSet(viewsets.ModelViewSet):
    permission_classes = (permissions.IsAuthenticated,)
    serializer_class = SubscriptionOrderSerializer
    http_method_names = ("get", "post", "head", "options")

    def get_queryset(self):
        return SubscriptionOrder.objects.filter(user=self.request.user).select_related("plan")
