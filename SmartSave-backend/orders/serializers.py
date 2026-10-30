from decimal import Decimal

from rest_framework import serializers

from marketplace.serializers import ProductListSerializer
from .models import Cart, CartItem, Order, OrderItem, OrderStatusLog


class CartItemSerializer(serializers.ModelSerializer):
    product_name = serializers.SerializerMethodField()
    product_image = serializers.SerializerMethodField()
    product_slug = serializers.SerializerMethodField()

    class Meta:
        model = CartItem
        fields = [
            "id", "product", "product_name", "product_slug",
            "product_image", "quantity", "unit_price", "total_price",
        ]
        read_only_fields = ["id", "unit_price", "total_price"]

    def get_product_name(self, obj):
        return obj.product.name

    def get_product_slug(self, obj):
        return obj.product.slug

    def get_product_image(self, obj):
        if obj.product.main_image:
            return obj.product.main_image.url
        return None

    def validate_quantity(self, value):
        if value <= 0:
            raise serializers.ValidationError("Quantity must be greater than zero.")
        return value

    def validate(self, data):
        product = data.get("product")
        cart = self.instance.cart if self.instance else None
        quantity = data.get("quantity", 1)
        if product and quantity > product.quantity:
            raise serializers.ValidationError(
                {"quantity": f"Only {product.quantity} {product.unit} available."}
            )
        if product and quantity < product.minimum_order:
            raise serializers.ValidationError(
                {"quantity": f"Minimum order is {product.minimum_order} {product.unit}."}
            )
        return data


class CartSerializer(serializers.ModelSerializer):
    items = CartItemSerializer(many=True, read_only=True)
    items_count = serializers.IntegerField(read_only=True)
    subtotal = serializers.DecimalField(max_digits=14, decimal_places=2, read_only=True)

    class Meta:
        model = Cart
        fields = ["id", "items", "items_count", "subtotal", "created_at", "updated_at"]


class AddToCartSerializer(serializers.Serializer):
    product_id = serializers.IntegerField()
    quantity = serializers.DecimalField(max_digits=10, decimal_places=2, min_value=Decimal("0.01"))

    def validate_product_id(self, value):
        from marketplace.models import Product
        try:
            product = Product.objects.get(
                id=value, is_active=True, availability_status="available"
            )
        except Product.DoesNotExist:
            raise serializers.ValidationError("Product not found or unavailable.")
        return value


class OrderItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderItem
        fields = [
            "id", "product", "product_name", "quantity",
            "unit_price", "total_price",
        ]


class OrderListSerializer(serializers.ModelSerializer):
    items_count = serializers.SerializerMethodField()
    buyer_name = serializers.SerializerMethodField()

    class Meta:
        model = Order
        fields = [
            "id", "order_number", "buyer", "buyer_name",
            "status", "payment_status", "subtotal", "delivery_fee",
            "total", "items_count", "ordered_at",
        ]

    def get_items_count(self, obj):
        return obj.items.count()

    def get_buyer_name(self, obj):
        return obj.buyer.get_full_name() or obj.buyer.email


class OrderDetailSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)
    buyer_name = serializers.SerializerMethodField()

    class Meta:
        model = Order
        fields = [
            "id", "order_number", "buyer", "buyer_name",
            "status", "payment_status",
            "delivery_address", "delivery_phone", "buyer_note",
            "subtotal", "delivery_fee", "total",
            "items", "ordered_at", "updated_at",
        ]

    def get_buyer_name(self, obj):
        return obj.buyer.get_full_name() or obj.buyer.email


class CheckoutSerializer(serializers.Serializer):
    delivery_address = serializers.CharField(required=True)
    delivery_phone = serializers.CharField(required=True)
    buyer_note = serializers.CharField(required=False, allow_blank=True)


class OrderStatusSerializer(serializers.Serializer):
    status = serializers.ChoiceField(
        choices=[
            "confirmed", "processing", "shipped",
            "delivered", "cancelled",
        ]
    )
    note = serializers.CharField(required=False, allow_blank=True)