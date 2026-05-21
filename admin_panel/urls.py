from django.urls import path
from . import views

urlpatterns = [
    path("", views.admin_dashboard, name="admin_dashboard"),
    path("users/", views.user_list, name="admin_users"),
    path("users/add/", views.user_create, name="admin_user_create"),
    path("users/<int:pk>/edit/", views.user_edit, name="admin_user_edit"),
    path("users/<int:pk>/deactivate/", views.user_deactivate, name="admin_user_deactivate"),
    path("users/<int:pk>/activate/", views.user_activate, name="admin_user_activate"),
    path("roles/", views.role_list, name="admin_roles"),
    path("roles/add/", views.role_create, name="admin_role_create"),
    path("roles/<int:pk>/edit/", views.role_edit, name="admin_role_edit"),
    path("audit/", views.audit_log_list, name="audit_log"),
    path("audit/export/pdf/", views.export_audit_pdf, name="export_audit_pdf"),
    path("settings/", views.settings_view, name="settings"),
    path("purchase-orders/", views.admin_purchase_orders, name="admin_purchase_orders"),
]
