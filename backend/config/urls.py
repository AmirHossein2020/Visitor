from django.contrib import admin
from django.conf import settings
from django.http import HttpResponseRedirect
from django.urls import include, path
from .views import health


def primary_admin_redirect(request):
    if settings.DEBUG:
        hostname = request.get_host().split(":", 1)[0]
        return HttpResponseRedirect(f"http://{hostname}:5173/platform-admin")
    return HttpResponseRedirect(f"{settings.FRONTEND_URL}/platform-admin")


urlpatterns = [
    path("health/", health, name="health"),
    path("admin/", primary_admin_redirect, name="primary-admin"),
    path("internal-django-admin/", admin.site.urls),
    path("api/", include("config.api_urls")),
]
