from django.contrib import admin
from django.urls import path, include
from django.contrib.auth import views as auth_views

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("accounts.urls")),
    path("dashboard/", include("inventory.urls")),
    path("admin-dashboard/", include("admin_panel.urls")),
    path("reports/", include("reports.urls")),
]
