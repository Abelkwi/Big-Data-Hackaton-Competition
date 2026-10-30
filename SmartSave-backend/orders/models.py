from django.conf import settings
from django.db import models
from django.utils.crypto import get_random_string


User = settings.AUTH_USER_MODEL


def generate_order_number():
    """Generate a unique order number like ORD-XXXXX."""
    return f"ORD-{get_random_string(8).upper()}"


class Cart(models.Model):
    """Shopping cart for a buyer. One active cart per user."""

    user = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name="cart"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Cart"
        verbose_name_plural = "Carts"

    @property
    def items_count(self):
        return self.items.count()

    @property
    def subtotal(self):
        return sum(item.total_price for item in self.items.all())

    def __str__(self):
        return f"Cart: {self.user.email} ({self.items_count} items)"


class CartItem(models.Model):
    """Individual item in a cart."""

    cart = models.ForeignKey(
        Cart, on_delete=models.CASCADE, related_name="items"
    )
    product = models.ForeignKey(
        "marketplace.Product", on_delete=models.CASCADE
    )
    quantity = models.DecimalField(max_digits=10, decimal_places=2)
    unit_price = models.DecimalField(max_digits=12, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Cart Item"
        verbose_name_plural = "Cart Items"
        unique_together = ("cart", "product")

    @property
    def total_price(self):
        return self.quantity * self.unit_price

    def __str__(self):
        return f"{self.product.name} x{self.quantity}"


class Order(models.Model):
    """Purchase order, possibly containing multiple items."""

    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("confirmed", "Confirmed"),
        ("processing", "Processing"),
        ("shipped", "Shipped"),
        ("delivered", "Delivered"),
        ("cancelled", "Cancelled"),
    ]

    PAYMENT_CHOICES = [
        ("pending", "Pending"),
        ("paid", "Paid"),
        ("failed", "Failed"),
        ("refunded", "Refunded"),
    ]

    order_number = models.CharField(
        max_length=20, unique=True, default=generate_order_number, editable=False
    )
    buyer = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="orders"
    )
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default="pending"
    )
    payment_status = models.CharField(
        max_length=20, choices=PAYMENT_CHOICES, default="pending"
    )

    # Contact & delivery
    delivery_address = models.TextField(blank=True)
    delivery_phone = models.CharField(max_length=20, blank=True)
    buyer_note = models.TextField(blank=True)

    # Financial
    subtotal = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    delivery_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total = models.DecimalField(max_digits=14, decimal_places=2, default=0)

    ordered_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-ordered_at"]
        verbose_name = "Order"
        verbose_name_plural = "Orders"

    def save(self, *args, **kwargs):
        if not self.total and self.subtotal:
            self.total = self.subtotal + self.delivery_fee
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.order_number} — {self.buyer.email}"


class OrderItem(models.Model):
    """Individual product within an order."""

    order = models.ForeignKey(
        Order, on_delete=models.CASCADE, related_name="items"
    )
    product = models.ForeignKey(
        "marketplace.Product", on_delete=models.SET_NULL, null=True
    )
    farmer = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, related_name="order_items"
    )
    product_name = models.CharField(max_length=150, blank=True)
    quantity = models.DecimalField(max_digits=10, decimal_places=2)
    unit_price = models.DecimalField(max_digits=12, decimal_places=2)
    total_price = models.DecimalField(max_digits=14, decimal_places=2)

    class Meta:
        verbose_name = "Order Item"
        verbose_name_plural = "Order Items"

    def save(self, *args, **kwargs):
        if not self.product_name and self.product:
            self.product_name = self.product.name
        if not self.farmer and self.product:
            self.farmer = self.product.farmer
        if not self.total_price:
            self.total_price = self.quantity * self.unit_price
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.product_name} x{self.quantity}"


class OrderStatusLog(models.Model):
    """Audit trail for order status changes."""

    order = models.ForeignKey(
        Order, on_delete=models.CASCADE, related_name="status_logs"
    )
    from_status = models.CharField(max_length=20, blank=True)
    to_status = models.CharField(max_length=20)
    changed_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True
    )
    note = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Order Status Log"
        verbose_name_plural = "Order Status Logs"

    def __str__(self):
        return f"{self.order.order_number}: {self.from_status} → {self.to_status}"