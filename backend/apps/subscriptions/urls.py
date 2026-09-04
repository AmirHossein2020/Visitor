from django.urls import path
from rest_framework.routers import DefaultRouter

from .views import ActivateTrialView, MySubscriptionView, PaymentInfoView, PaymentViewSet, PlanListView, SubscriptionOrderViewSet


router = DefaultRouter()
router.register("orders", SubscriptionOrderViewSet, basename="subscription-order")
router.register("payments", PaymentViewSet, basename="subscription-payment")

urlpatterns = [
    path("plans/", PlanListView.as_view(), name="plan-list"),
    path("me/", MySubscriptionView.as_view(), name="my-subscription"),
    path("trial/activate/", ActivateTrialView.as_view(), name="trial-activate"),
    path("payment-info/", PaymentInfoView.as_view(), name="payment-info"),
] + router.urls
