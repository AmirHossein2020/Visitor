from datetime import datetime, time, timedelta
from decimal import Decimal

from django.db.models import Count, DecimalField, Q, Sum, Value
from django.db.models.functions import Coalesce
from django.utils import timezone
from rest_framework import permissions
from apps.subscriptions.permissions import HasActiveSubscription
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.invoices.models import Invoice, InvoiceItem
from apps.products.models import Product
from apps.purchases.models import Purchase

from .models import SalesOrder, SalesReturn


MONEY_FIELD = DecimalField(max_digits=20, decimal_places=2)
ZERO_MONEY = Value(Decimal("0.00"), output_field=MONEY_FIELD)


def month_start(day):
    return day.replace(day=1)


def parse_range(request, *, default="month"):
    from_value = request.query_params.get("from")
    to_value = request.query_params.get("to")
    if bool(from_value) != bool(to_value):
        raise ValidationError("تاریخ شروع و پایان را با هم وارد کنید.")
    if from_value:
        try:
            start = datetime.strptime(from_value, "%Y-%m-%d").date()
            end = datetime.strptime(to_value, "%Y-%m-%d").date()
        except ValueError:
            raise ValidationError("قالب تاریخ باید YYYY-MM-DD باشد.")
        if start > end:
            raise ValidationError("تاریخ شروع نمی‌تواند بعد از تاریخ پایان باشد.")
        return start, end
    today = timezone.localdate()
    return (today, today) if default == "today" else (month_start(today), today)


def date_bounds(start, end):
    tz = timezone.get_current_timezone()
    return (
        timezone.make_aware(datetime.combine(start, time.min), tz),
        timezone.make_aware(datetime.combine(end + timedelta(days=1), time.min), tz),
    )


def summary_for(user, start, end):
    start_dt, end_dt = date_bounds(start, end)
    invoices = Invoice.objects.filter(
        owner=user, status=Invoice.Status.ISSUED,
        issued_at__gte=start_dt, issued_at__lt=end_dt,
    )
    purchases = Purchase.objects.filter(
        owner=user, status=Purchase.Status.CONFIRMED,
        purchase_date__gte=start, purchase_date__lte=end,
    )
    returns = SalesReturn.objects.filter(
        owner=user, status=SalesReturn.Status.CONFIRMED,
        created_at__gte=start_dt, created_at__lt=end_dt,
    )
    orders = SalesOrder.objects.filter(
        owner=user, created_at__gte=start_dt, created_at__lt=end_dt,
    )
    sales = invoices.aggregate(total=Coalesce(Sum("final_amount"), ZERO_MONEY))["total"]
    purchase_total = purchases.aggregate(total=Coalesce(Sum("total_amount"), ZERO_MONEY))["total"]
    return_total = returns.aggregate(total=Coalesce(Sum("total_amount"), ZERO_MONEY))["total"]
    return {
        "from": start, "to": end,
        "sales_total": sales,
        "purchase_total": purchase_total,
        "return_total": return_total,
        "net_sales": sales - return_total,
        "invoices_count": invoices.count(),
        "orders_count": orders.count(),
        "purchases_count": purchases.count(),
        "returns_count": returns.count(),
    }


class DashboardView(APIView):
    permission_classes = (permissions.IsAuthenticated, HasActiveSubscription)

    def get(self, request):
        today = timezone.localdate()
        selected_start, selected_end = parse_range(request)
        products = Product.objects.filter(owner=request.user).annotate(
            current_stock=Coalesce(
                Sum("stock_movements__quantity"),
                Value(Decimal("0.000")),
                output_field=DecimalField(max_digits=18, decimal_places=3),
            )
        )
        recent_orders = SalesOrder.objects.filter(owner=request.user).select_related("customer")[:5]
        recent_purchases = Purchase.objects.filter(owner=request.user).select_related("customer")[:5]
        recent_returns = SalesReturn.objects.filter(owner=request.user).select_related("invoice")[:5]
        return Response({
            "today": summary_for(request.user, today, today),
            "current_month": summary_for(request.user, selected_start, selected_end),
            "inventory": {
                "total_products": products.count(),
                "negative_stock_count": products.filter(current_stock__lt=0).count(),
                "zero_stock_count": products.filter(current_stock=0).count(),
            },
            "recent_activity": {
                "orders": [{"id": item.id, "customer_name": item.customer.name, "status": item.get_status_display(), "total_amount": item.total_amount, "created_at": item.created_at} for item in recent_orders],
                "purchases": [{"id": item.id, "customer_name": item.customer.name, "status": item.get_status_display(), "total_amount": item.total_amount, "created_at": item.created_at} for item in recent_purchases],
                "returns": [{"id": item.id, "customer_name": item.invoice.buyer_name, "status": item.get_status_display(), "total_amount": item.total_amount, "created_at": item.created_at} for item in recent_returns],
            },
        })


class SummaryReportView(APIView):
    permission_classes = (permissions.IsAuthenticated, HasActiveSubscription)

    def get(self, request):
        start, end = parse_range(request)
        return Response(summary_for(request.user, start, end))


class ProductSalesReportView(APIView):
    permission_classes = (permissions.IsAuthenticated, HasActiveSubscription)

    def get(self, request):
        start, end = parse_range(request)
        start_dt, end_dt = date_bounds(start, end)
        rows = InvoiceItem.objects.filter(
            invoice__owner=request.user,
            invoice__status=Invoice.Status.ISSUED,
            invoice__issued_at__gte=start_dt,
            invoice__issued_at__lt=end_dt,
        ).values("product_name", "brand", "unit").annotate(
            quantity_sold=Sum("quantity"),
            total_sales=Coalesce(Sum("line_total"), ZERO_MONEY),
        ).order_by("-quantity_sold", "product_name")[:50]
        return Response(list(rows))


class CustomerSalesReportView(APIView):
    permission_classes = (permissions.IsAuthenticated, HasActiveSubscription)

    def get(self, request):
        start, end = parse_range(request)
        start_dt, end_dt = date_bounds(start, end)
        rows = Invoice.objects.filter(
            owner=request.user, status=Invoice.Status.ISSUED,
            issued_at__gte=start_dt, issued_at__lt=end_dt,
        ).values("sales_order__customer_id", "buyer_name", "buyer_company_name").annotate(
            invoice_count=Count("id"),
            total_sales=Coalesce(Sum("final_amount"), ZERO_MONEY),
        ).order_by("-total_sales", "buyer_name")[:50]
        return Response(list(rows))
