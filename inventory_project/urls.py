from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("accounts.urls")),
    path("dashboard/", include("inventory.urls")),
    path("admin-dashboard/", include("admin_panel.urls")),
    path("reports/", include("reports.urls")),
]
