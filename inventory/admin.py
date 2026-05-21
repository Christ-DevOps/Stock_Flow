from django.contrib import admin
from django.db.models import Sum, Count, F, ExpressionWrapper, DecimalField
from .models import (
    Category, Supplier, Product, ProductVariant,
    StockMovement, PurchaseOrder, Notification,
)
from decimal import Decimal


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ["name", "product_count_inline", "total_value_inline", "created_at"]
    search_fields = ["name"]
    ordering = ["name"]
    date_hierarchy = "created_at"

    def product_count_inline(self, obj):
        return obj.product_set.count()
    product_count_inline.short_description = "Products"

    def total_value_inline(self, obj):
        total = Decimal("0")
        for p in obj.product_set.all():
            total += p.total_value
        return f"${total:.2f}" if total else "$0.00"
    total_value_inline.short_description = "Total Value"


@admin.register(Supplier)
class SupplierAdmin(admin.ModelAdmin):
    list_display = ["name", "contact_person", "email", "phone", "is_active", "created_at"]
    list_filter = ["is_active", "created_at"]
    search_fields = ["name", "contact_person", "email"]
    ordering = ["name"]


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = [
        "name", "sku", "category", "supplier",
        "quantity", "unit", "stock_status_emoji", "price", "cost_price",
        "total_value", "status",
    ]
    list_filter = ["status", "category", "supplier", "unit"]
    search_fields = ["name", "sku", "barcode"]
    ordering = ["-updated_at"]
    readonly_fields = ["total_value", "created_at", "updated_at"]
    list_editable = ["status", "quantity"]

    fieldsets = (
        ("Basic Info", {"fields": ("name", "description", "category", "supplier")}),
        ("Identification", {"fields": ("sku", "barcode")}),
        ("Pricing", {"fields": ("price", "cost_price")}),
        ("Stock", {"fields": ("quantity", "unit", "low_stock_threshold", "max_stock_threshold", "status")}),
        ("Media", {"fields": ("image",)}),
        ("Audit", {"fields": ("created_at", "updated_at"), "classes": ("collapse",)}),
    )

    def stock_status_emoji(self, obj):
        s = obj.stock_status
        return {"low": "🔴 Low", "overstock": "🟡 Overstock", "ok": "🟢 OK"}[s]
    stock_status_emoji.short_description = "Status"


@admin.register(ProductVariant)
class ProductVariantAdmin(admin.ModelAdmin):
    list_display = ["product", "variant_name", "variant_value", "sku", "price", "quantity"]
    list_filter = ["variant_name"]
    search_fields = ["product__name", "variant_value"]
    ordering = ["product__name", "variant_value"]


@admin.register(StockMovement)
class StockMovementAdmin(admin.ModelAdmin):
    list_display = ["product", "movement_type_badge", "qty_badge", "reason", "recorded_by", "date"]
    list_filter = ["movement_type", "reason", "date"]
    search_fields = ["product__name", "recorded_by"]
    ordering = ["-date"]
    date_hierarchy = "date"

    def movement_type_badge(self, obj):
        colors = {"IN": "success", "OUT": "danger", "ADJUST": "warning", "RETURN_IN": "info", "RETURN_OUT": "secondary"}
        c = colors.get(obj.movement_type, "secondary")
        return f'<span class="badge bg-{c}">{obj.get_movement_type_display()}</span>'
    movement_type_badge.short_description = "Type"
    movement_type_badge.admin_order_field = "movement_type"
    movement_type_badge.allow_tags = True

    def qty_badge(self, obj):
        pos = obj.movement_type in ("IN", "RETURN_IN")
        cls = "success" if pos else "danger"
        sign = "+" if pos else "−"
        return f'<span class="badge bg-{cls}">{sign}{obj.quantity}</span>'
    qty_badge.short_description = "Qty"
    qty_badge.allow_tags = True

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("product", "product__category")


@admin.register(PurchaseOrder)
class PurchaseOrderAdmin(admin.ModelAdmin):
    list_display = ["order_number", "supplier", "product", "quantity",
                    "unit_price", "total_amount", "status", "order_date"]
    list_filter = ["status", "order_date", "supplier"]
    search_fields = ["order_number", "product__name", "supplier__name"]
    ordering = ["-order_date"]
    actions = ["mark_received"]
    date_hierarchy = "order_date"

    def mark_received(self, request, queryset):
        for order in queryset.filter(status__in=["draft", "sent"]):
            order.status = "received"
            order.received_date = timezone.now()
            order.save()
            StockMovement.objects.create(
                product=order.product, movement_type="IN", quantity=order.quantity,
                reason="delivery", notes=f"PO: {order.order_number}",
                recorded_by=request.user.username,
            )
        self.message_user(request, f"{queryset.count()} order(s) marked as received.")
    mark_received.short_description = "Mark selected as received"


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ["notification_type", "title", "product", "is_read", "created_at"]
    list_filter = ["notification_type", "is_read", "created_at"]
    search_fields = ["title", "message"]
    ordering = ["-created_at"]
    actions = ["mark_all_read"]
    date_hierarchy = "created_at"

    def mark_all_read(self, request, queryset):
        queryset.update(is_read=True)
        self.message_user(request, f"{queryset.count()} notification(s) marked as read.")
    mark_all_read.short_description = "Mark selected as read"
