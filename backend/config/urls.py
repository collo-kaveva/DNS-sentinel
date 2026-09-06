from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/auth/", include("apps.accounts.urls")),
    path("api/", include("apps.dns_intelligence.urls")),
    path("api/lifecycle/", include("apps.lifecycle.urls")),
    path("api/investigation/", include("apps.investigation.urls")),
]
