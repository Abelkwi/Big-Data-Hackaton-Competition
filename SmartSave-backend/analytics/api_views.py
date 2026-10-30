from django.contrib.auth import get_user_model
from django.db.models import Count, Sum
from rest_framework import permissions
from rest_framework.response import Response
from rest_framework.views import APIView

from marketplace.models import Product
from orders.models import Order

User = get_user_model()


class AnalyticsOverviewView(APIView):
    """Overall platform analytics."""
    permission_classes = [permissions.IsAdminUser]

    def get(self, request):
        total_users = User.objects.count()
        farmers = User.objects.filter(role="farmer").count()
        buyers = User.objects.filter(role="buyer").count()
        ngos = User.objects.filter(role="ngo").count()
        products = Product.objects.filter(is_active=True).count()
        orders = Order.objects.count()
        delivered = Order.objects.filter(status="delivered").count()
        revenue = Order.objects.filter(status="delivered").aggregate(
            Sum("total")
        )["total__sum"] or 0

        return Response({
            "total_users": total_users,
            "farmers": farmers,
            "buyers": buyers,
            "ngos": ngos,
            "products": products,
            "orders": orders,
            "delivered_orders": delivered,
            "total_revenue": str(revenue),
        })


class UserAnalyticsView(APIView):
    """User registration analytics."""
    permission_classes = [permissions.IsAdminUser]

    def get(self, request):
        by_role = list(
            User.objects.values("role")
            .annotate(count=Count("id"))
            .order_by("role")
        )
        by_verification = {
            "verified": User.objects.filter(is_verified=True).count(),
            "unverified": User.objects.filter(is_verified=False).count(),
        }
        return Response({"by_role": by_role, "by_verification": by_verification})


class ProductAnalyticsView(APIView):
    """Product analytics."""
    permission_classes = [permissions.IsAdminUser]

    def get(self, request):
        by_category = list(
            Product.objects.filter(is_active=True)
            .values("category__name")
            .annotate(count=Count("id"))
            .order_by("-count")
        )
        by_verification = list(
            Product.objects.values("verification_status")
            .annotate(count=Count("id"))
            .order_by("verification_status")
        )
        total_views = Product.objects.aggregate(Sum("views"))["views__sum"] or 0
        return Response({
            "by_category": by_category,
            "by_verification": by_verification,
            "total_views": total_views,
        })


class OrderAnalyticsView(APIView):
    """Order analytics."""
    permission_classes = [permissions.IsAdminUser]

    def get(self, request):
        by_status = list(
            Order.objects.values("status")
            .annotate(count=Count("id"))
            .order_by("status")
        )
        total_revenue = Order.objects.filter(status="delivered").aggregate(
            Sum("total")
        )["total__sum"] or 0
        return Response({
            "by_status": by_status,
            "total_revenue": str(total_revenue),
        })


class TopCropsView(APIView):
    """Most listed product categories."""
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        top = list(
            Product.objects.filter(is_active=True)
            .values("category__name")
            .annotate(count=Count("id"))
            .order_by("-count")[:10]
        )
        return Response(top)


class ActiveDistrictsView(APIView):
    """Most active districts by product listings."""
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        districts = list(
            Product.objects.filter(is_active=True, district__gt="")
            .values("district")
            .annotate(count=Count("id"))
            .order_by("-count")[:10]
        )
        return Response(districts)