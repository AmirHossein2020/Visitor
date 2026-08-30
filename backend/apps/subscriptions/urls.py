from django.urls import path
from rest_framework.routers import DefaultRouter

from .views import MySubscriptionView, PlanListView, SubscriptionOrderViewSet


router = DefaultRouter()
router.register("orders", SubscriptionOrderViewSet, basename="subscription-order")

urlpatterns = [
    path("plans/", PlanListView.as_view(), name="plan-list"),
    path("me/", MySubscriptionView.as_view(), name="my-subscription"),
] + router.urls
