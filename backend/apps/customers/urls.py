from rest_framework.routers import SimpleRouter

from .views import CustomerViewSet


router = SimpleRouter()
router.register("", CustomerViewSet, basename="customer")

urlpatterns = router.urls
