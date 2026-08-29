from rest_framework.routers import SimpleRouter

from .views import PurchaseViewSet


router = SimpleRouter()
router.register("", PurchaseViewSet, basename="purchase")

urlpatterns = router.urls
