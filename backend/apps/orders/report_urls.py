from django.urls import path

from .report_views import CustomerSalesReportView, ProductSalesReportView, SummaryReportView


urlpatterns = [
    path("summary/", SummaryReportView.as_view(), name="report-summary"),
    path("products/", ProductSalesReportView.as_view(), name="report-products"),
    path("customers/", CustomerSalesReportView.as_view(), name="report-customers"),
]
