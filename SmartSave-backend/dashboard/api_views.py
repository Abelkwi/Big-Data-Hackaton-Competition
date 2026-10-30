from django.contrib.auth import get_user_model
from django.db.models import Count, Sum, Avg
from rest_framework import permissions
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.models import FarmerFollow
from marketplace.models import Product, Review, Wishlist
from orders.models import Order

User = get_user_model()


class FarmerDashboardView(APIView):
    """Aggregated dashboard data for farmers."""
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        if request.user.role != "farmer":
            return Response({"detail": "Not a farmer account."}, status=403)

        products = Product.objects.filter(farmer=request.user)
        orders = Order.objects.filter(product__farmer=request.user)
        reviews = Review.objects.filter(product__farmer=request.user, is_approved=True)

        data = {
            "active_listings": products.filter(is_active=True).count(),
            "total_orders": orders.count(),
            "pending_orders": orders.filter(status="pending").count(),
            "total_revenue": str(
                orders.filter(status="delivered").aggregate(Sum("total_price"))["total_price__sum"] or 0
            ),
            "average_rating": round(reviews.aggregate(Avg("rating"))["rating__avg"] or 0, 1),
            "followers": FarmerFollow.objects.filter(farmer=request.user).count(),
            "unread_messages": 0,
            "recent_orders": list(orders.order_by("-ordered_at")[:5].values(
                "id", "product__name", "quantity", "total_price", "status", "ordered_at"
            )),
        }
        return Response(data)


class BuyerDashboardView(APIView):
    """Aggregated dashboard data for buyers."""
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        if request.user.role != "buyer":
            return Response({"detail": "Not a buyer account."}, status=403)

        orders = Order.objects.filter(buyer=request.user)
        wishlist_count = Wishlist.objects.filter(user=request.user).count()

        data = {
            "total_orders": orders.count(),
            "pending_orders": orders.filter(status="pending").count(),
            "delivered_orders": orders.filter(status="delivered").count(),
            "total_spent": str(
                orders.filter(status="delivered").aggregate(Sum("total_price"))["total_price__sum"] or 0
            ),
            "wishlist_count": wishlist_count,
            "unread_messages": 0,
            "recent_orders": list(orders.order_by("-ordered_at")[:5].values(
                "id", "product__name", "quantity", "total_price", "status", "ordered_at"
            )),
        }
        return Response(data)


class NGODashboardView(APIView):
    """Aggregated dashboard data for NGOs."""
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        if request.user.role != "ngo":
            return Response({"detail": "Not an NGO account."}, status=403)

        data = {
            "total_farmers": User.objects.filter(role="farmer", is_active=True).count(),
            "active_recoveries": 0,
            "completed_projects": 0,
            "total_donations": 0,
        }
        return Response(data)


class AdminDashboardView(APIView):
    """Aggregated dashboard data for administrators."""
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        if not request.user.is_staff:
            return Response({"detail": "Not an admin account."}, status=403)

        data = {
            "total_users": User.objects.count(),
            "farmers": User.objects.filter(role="farmer").count(),
            "buyers": User.objects.filter(role="buyer").count(),
            "ngos": User.objects.filter(role="ngo").count(),
            "total_products": Product.objects.count(),
            "pending_verification": Product.objects.filter(verification_status="pending").count(),
            "total_orders": Order.objects.count(),
            "pending_orders": Order.objects.filter(status="pending").count(),
            "total_revenue": str(
                Order.objects.filter(status="delivered").aggregate(Sum("total_price"))["total_price__sum"] or 0
            ),
        }
        return Response(data)