from rest_framework.routers import SimpleRouter

from .views import SalesOrderViewSet


router = SimpleRouter()
router.register("", SalesOrderViewSet, basename="sales-order")

urlpatterns = router.urls
