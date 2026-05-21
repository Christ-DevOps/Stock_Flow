from django.urls import path
from inventory.views import reports_view, export_excel, export_pdf

app_name = "reports"

urlpatterns = [
    path("", reports_view, name="reports"),
    path("export/xlsx/", export_excel, name="export_excel"),
    path("export/pdf/", export_pdf, name="export_pdf"),
]
