from django.contrib import admin

from .models import Cart, CartItem, Order, OrderItem, OrderStatusLog


class CartItemInline(admin.TabularInline):
    model = CartItem
    extra = 0
    readonly_fields = ("product", "quantity", "unit_price", "total_price")


@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "items_count", "created_at")
    search_fields = ("user__email", "user__username")
    readonly_fields = ("created_at", "updated_at")
    inlines = [CartItemInline]

    def items_count(self, obj):
        return obj.items.count()
    items_count.short_description = "Items"


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ("product", "product_name", "quantity", "unit_price", "total_price")


class OrderStatusLogInline(admin.TabularInline):
    model = OrderStatusLog
    extra = 0
    readonly_fields = ("from_status", "to_status", "changed_by", "note", "created_at")
    can_delete = False


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = (
        "order_number", "buyer", "status", "payment_status",
        "total", "items_count", "ordered_at",
    )
    list_filter = ("status", "payment_status", "ordered_at")
    search_fields = ("order_number", "buyer__email", "buyer__username")
    readonly_fields = (
        "order_number", "subtotal", "delivery_fee", "total",
        "ordered_at", "updated_at",
    )
    ordering = ("-ordered_at",)
    inlines = [OrderItemInline, OrderStatusLogInline]

    def items_count(self, obj):
        return obj.items.count()
    items_count.short_description = "Items"

    actions = ["mark_confirmed", "mark_shipped", "mark_delivered"]

    def mark_confirmed(self, request, queryset):
        updated = queryset.update(status="confirmed")
        self.message_user(request, f"{updated} orders confirmed.")
    mark_confirmed.short_description = "Mark selected as Confirmed"

    def mark_shipped(self, request, queryset):
        updated = queryset.update(status="shipped")
        self.message_user(request, f"{updated} orders shipped.")
    mark_shipped.short_description = "Mark selected as Shipped"

    def mark_delivered(self, request, queryset):
        updated = queryset.update(status="delivered")
        self.message_user(request, f"{updated} orders delivered.")
    mark_delivered.short_description = "Mark selected as Delivered"


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ("id", "order", "product_name", "farmer", "quantity", "unit_price", "total_price")
    list_filter = ("farmer",)
    search_fields = ("product_name", "order__order_number", "farmer__email")
    readonly_fields = ("product_name", "quantity", "unit_price", "total_price")