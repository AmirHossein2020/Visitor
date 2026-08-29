from rest_framework.routers import SimpleRouter

from .views import SellerProfileViewSet


router = SimpleRouter()
router.register("", SellerProfileViewSet, basename="seller-profile")

urlpatterns = router.urls
