from django.urls import include, path
from rest_framework.routers import DefaultRouter
from .views import TicketViewSet, attachment_download

router = DefaultRouter()
router.register("tickets", TicketViewSet, basename="support-ticket")
urlpatterns = [path("attachments/<int:pk>/download/", attachment_download), path("", include(router.urls))]
