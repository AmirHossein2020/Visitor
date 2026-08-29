from rest_framework.routers import SimpleRouter

from .return_views import SalesReturnViewSet


router = SimpleRouter()
router.register("", SalesReturnViewSet, basename="sales-return")

urlpatterns = router.urls
