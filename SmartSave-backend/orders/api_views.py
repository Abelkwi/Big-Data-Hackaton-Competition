from decimal import Decimal
from django.db import transaction
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from marketplace.models import Product
from .models import Cart, CartItem, Order, OrderItem, OrderStatusLog
from .serializers import (
    CartSerializer,
    CartItemSerializer,
    AddToCartSerializer,
    OrderListSerializer,
    OrderDetailSerializer,
    CheckoutSerializer,
    OrderStatusSerializer,
)


class IsBuyer(permissions.BasePermission):
    """Allow access only to buyers."""
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == "buyer"


class IsFarmerOrAdmin(permissions.BasePermission):
    """Allow access to farmer or admin for order management."""
    def has_permission(self, request, view):
        return request.user.is_authenticated and (
            request.user.role == "farmer" or request.user.is_staff
        )


# ─── CART ─────────────────────────────────────────────────────


class CartView(APIView):
    """Get current user's cart."""
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        cart, _ = Cart.objects.get_or_create(user=request.user)
        serializer = CartSerializer(cart)
        return Response(serializer.data)


class AddToCartView(APIView):
    """Add a product to cart."""
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = AddToCartSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        product = Product.objects.get(
            id=serializer.validated_data["product_id"],
            is_active=True,
            availability_status="available",
        )
        quantity = serializer.validated_data["quantity"]

        if quantity < product.minimum_order:
            return Response(
                {"quantity": f"Minimum order is {product.minimum_order} {product.unit}."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if quantity > product.quantity:
            return Response(
                {"quantity": f"Only {product.quantity} {product.unit} available."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        cart, _ = Cart.objects.get_or_create(user=request.user)

        cart_item, created = CartItem.objects.get_or_create(
            cart=cart,
            product=product,
            defaults={"quantity": quantity, "unit_price": product.price_per_unit},
        )
        if not created:
            cart_item.quantity = quantity
            cart_item.unit_price = product.price_per_unit
            cart_item.save()

        return Response(
            CartSerializer(cart).data,
            status=status.HTTP_200_OK if not created else status.HTTP_201_CREATED,
        )


class UpdateCartItemView(APIView):
    """Update quantity of a cart item."""
    permission_classes = [permissions.IsAuthenticated]

    def put(self, request, item_id):
        try:
            cart_item = CartItem.objects.get(
                id=item_id, cart__user=request.user
            )
        except CartItem.DoesNotExist:
            return Response(
                {"detail": "Cart item not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        quantity = request.data.get("quantity")
        if not quantity:
            return Response(
                {"quantity": "Quantity is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            quantity = Decimal(str(quantity))
        except Exception:
            return Response(
                {"quantity": "Invalid quantity."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if quantity <= 0:
            cart_item.delete()
            cart = CartSerializer(cart_item.cart)
            return Response(cart.data)

        product = cart_item.product
        if quantity > product.quantity:
            return Response(
                {"quantity": f"Only {product.quantity} {product.unit} available."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        cart_item.quantity = quantity
        cart_item.save()
        cart = CartSerializer(cart_item.cart)
        return Response(cart.data)


class RemoveFromCartView(APIView):
    """Remove an item from cart."""
    permission_classes = [permissions.IsAuthenticated]

    def delete(self, request, item_id):
        try:
            cart_item = CartItem.objects.get(
                id=item_id, cart__user=request.user
            )
        except CartItem.DoesNotExist:
            return Response(
                {"detail": "Cart item not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        cart_item.delete()
        cart = CartSerializer(cart_item.cart)
        return Response(cart.data)


class ClearCartView(APIView):
    """Remove all items from cart."""
    permission_classes = [permissions.IsAuthenticated]

    def delete(self, request):
        cart, _ = Cart.objects.get_or_create(user=request.user)
        cart.items.all().delete()
        return Response({"detail": "Cart cleared."})


# ─── CHECKOUT ────────────────────────────────────────────────


class CheckoutView(APIView):
    """Convert cart to order."""
    permission_classes = [permissions.IsAuthenticated]

    @transaction.atomic
    def post(self, request):
        serializer = CheckoutSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        try:
            cart = Cart.objects.get(user=request.user)
        except Cart.DoesNotExist:
            return Response(
                {"detail": "Your cart is empty."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        cart_items = cart.items.select_related("product__farmer").all()
        if not cart_items:
            return Response(
                {"detail": "Your cart is empty."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        subtotal = sum(item.total_price for item in cart_items)

        order = Order.objects.create(
            buyer=request.user,
            subtotal=subtotal,
            delivery_fee=Decimal("0"),
            total=subtotal,
            delivery_address=serializer.validated_data["delivery_address"],
            delivery_phone=serializer.validated_data["delivery_phone"],
            buyer_note=serializer.validated_data.get("buyer_note", ""),
        )

        # Create OrderItems and reduce stock
        for cart_item in cart_items:
            product = cart_item.product
            OrderItem.objects.create(
                order=order,
                product=product,
                farmer=product.farmer,
                product_name=product.name,
                quantity=cart_item.quantity,
                unit_price=cart_item.unit_price,
                total_price=cart_item.total_price,
            )

            # Reduce available quantity
            if product.quantity is not None:
                product.quantity -= cart_item.quantity
                if product.quantity <= 0:
                    product.availability_status = "out_of_stock"
                product.save()

        # Log initial status
        OrderStatusLog.objects.create(
            order=order,
            from_status="",
            to_status="pending",
            changed_by=request.user,
        )

        # Clear cart
        cart.items.all().delete()

        return Response(
            OrderDetailSerializer(order).data,
            status=status.HTTP_201_CREATED,
        )


# ─── ORDER LIST / DETAIL ─────────────────────────────────────


class MyOrderListView(generics.ListAPIView):
    """List current user's orders (buyer sees own, farmer sees their sales)."""
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = OrderListSerializer

    def get_queryset(self):
        user = self.request.user
        if user.role == "farmer":
            return Order.objects.filter(
                items__farmer=user
            ).distinct().prefetch_related("items")
        return Order.objects.filter(buyer=user).prefetch_related("items")


class OrderDetailView(APIView):
    """Get full order detail."""
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, id):
        try:
            order = Order.objects.prefetch_related(
                "items__product", "status_logs"
            ).get(id=id)
        except Order.DoesNotExist:
            return Response(
                {"detail": "Order not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        # Authorization: buyer, farmer who has items in order, or admin
        is_buyer = order.buyer == request.user
        is_farmer = order.items.filter(farmer=request.user).exists()
        is_admin = request.user.is_staff

        if not (is_buyer or is_farmer or is_admin):
            return Response(
                {"detail": "Permission denied."},
                status=status.HTTP_403_FORBIDDEN,
            )

        data = OrderDetailSerializer(order).data
        data["status_logs"] = [
            {
                "from_status": log.from_status,
                "to_status": log.to_status,
                "changed_by": log.changed_by.email if log.changed_by else None,
                "note": log.note,
                "created_at": log.created_at,
            }
            for log in order.status_logs.all()
        ]
        return Response(data)


class CancelOrderView(APIView):
    """Cancel an order (buyer only, within pending status)."""
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, id):
        try:
            order = Order.objects.get(id=id, buyer=request.user, status="pending")
        except Order.DoesNotExist:
            return Response(
                {"detail": "Order not found or cannot be cancelled."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        order.status = "cancelled"
        order.save()

        OrderStatusLog.objects.create(
            order=order,
            from_status="pending",
            to_status="cancelled",
            changed_by=request.user,
            note=request.data.get("note", ""),
        )

        return Response({"detail": "Order cancelled.", "status": "cancelled"})


# ─── ORDER STATUS MANAGEMENT (Farmer / Admin) ────────────────


class UpdateOrderStatusView(APIView):
    """Update order status (farmer with items in order, or admin)."""
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, id):
        try:
            order = Order.objects.get(id=id)
        except Order.DoesNotExist:
            return Response(
                {"detail": "Order not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        is_farmer = order.items.filter(farmer=request.user).exists()
        if not (is_farmer or request.user.is_staff):
            return Response(
                {"detail": "Permission denied."},
                status=status.HTTP_403_FORBIDDEN,
            )

        serializer = OrderStatusSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        new_status = serializer.validated_data["status"]
        valid_transitions = {
            "pending": ["confirmed", "cancelled"],
            "confirmed": ["processing", "cancelled"],
            "processing": ["shipped", "cancelled"],
            "shipped": ["delivered"],
            "delivered": [],
            "cancelled": [],
        }

        if new_status not in valid_transitions.get(order.status, []):
            return Response(
                {
                    "detail": f"Cannot change from '{order.status}' to '{new_status}'."
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        old_status = order.status
        order.status = new_status
        order.save()

        OrderStatusLog.objects.create(
            order=order,
            from_status=old_status,
            to_status=new_status,
            changed_by=request.user,
            note=serializer.validated_data.get("note", ""),
        )

        return Response(
            {"detail": f"Order status updated to '{new_status}'.", "status": new_status}
        )


class FarmerOrderListView(generics.ListAPIView):
    """List orders for farmer's products."""
    permission_classes = [IsFarmerOrAdmin]
    serializer_class = OrderListSerializer

    def get_queryset(self):
        return Order.objects.filter(
            items__farmer=self.request.user
        ).distinct().prefetch_related("items").order_by("-ordered_at")