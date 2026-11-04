from datetime import datetime
from zoneinfo import ZoneInfo

from django.contrib.auth import get_user_model
from django.db.models import Count, Sum, Avg
from django.utils import timezone
from rest_framework import permissions
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.models import FarmerFollow
from messaging.models import Message
from marketplace.models import Product, Review, Wishlist
from notifications.models import Notification
from orders.models import Order, OrderItem

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

        kigali = ZoneInfo("Africa/Kigali")
        now = timezone.now().astimezone(kigali)
        orders = Order.objects.filter(buyer=request.user).prefetch_related(
            "items__product__category",
            "items__farmer__profile__farmer_profile",
        )
        wishlist_count = Wishlist.objects.filter(user=request.user).count()
        delivered_orders = orders.filter(status="delivered")
        unread_messages = Message.objects.filter(
            conversation__participants=request.user,
            is_read=False,
        ).exclude(sender=request.user).distinct().count()
        notifications = Notification.objects.filter(
            recipient=request.user
        ).order_by("-created_at")

        monthly_spend = []
        monthly_order_count = 0
        previous_month_order_count = 0
        current_month_spend = 0
        previous_month_spend = 0
        for offset in range(5, -1, -1):
            month_index = now.year * 12 + now.month - 1 - offset
            year, month = divmod(month_index, 12)
            month_start = datetime(year, month + 1, 1, tzinfo=kigali)
            next_year, next_month = (
                (year + 1, 1) if month == 11 else (year, month + 2)
            )
            month_end = datetime(next_year, next_month, 1, tzinfo=kigali)
            range_orders = orders.filter(
                ordered_at__gte=month_start,
                ordered_at__lt=month_end,
            )
            spend = range_orders.filter(status="delivered").aggregate(
                total=Sum("total")
            )["total"] or 0
            monthly_spend.append({
                "month": month_start.strftime("%b"),
                "total": str(spend),
            })
            if offset == 0:
                monthly_order_count = range_orders.count()
                current_month_spend = spend
            elif offset == 1:
                previous_month_spend = spend
                previous_month_order_count = range_orders.count()

        recent_orders = []
        for order in orders.order_by("-ordered_at")[:5]:
            items = list(order.items.all())
            names = list(dict.fromkeys(
                item.product_name or (item.product.name if item.product else "Produce")
                for item in items
            ))
            supplier = None
            for item in items:
                farmer = item.farmer
                if farmer:
                    supplier = (
                        farmer.profile.farmer_profile.store_name
                        if hasattr(farmer, "profile")
                        and hasattr(farmer.profile, "farmer_profile")
                        and farmer.profile.farmer_profile.store_name
                        else farmer.get_full_name() or farmer.email
                    )
            recent_orders.append({
                "id": order.id,
                "order_number": order.order_number,
                "product_name": ", ".join(names[:2]) or "Order",
                "supplier": supplier or "SMARTSAVE marketplace",
                "quantity": str(sum((item.quantity for item in items), 0)),
                "total": str(order.total),
                "status": order.status,
                "ordered_at": order.ordered_at,
                "delivery_address": order.delivery_address,
            })

        categories = {}
        for order in delivered_orders.prefetch_related("items__product__category"):
            for item in order.items.all():
                category = (
                    item.product.category.name
                    if item.product and item.product.category
                    else "Other"
                )
                categories[category] = categories.get(category, 0) + item.total_price

        total_spent = delivered_orders.aggregate(total=Sum("total"))["total"] or 0
        year_start = datetime(now.year, 1, 1, tzinfo=kigali)
        year_spent = delivered_orders.filter(
            ordered_at__gte=year_start
        ).aggregate(total=Sum("total"))["total"] or 0
        monthly_average = year_spent / now.month
        monthly_growth = (
            round((current_month_spend - previous_month_spend) * 100 / previous_month_spend, 1)
            if previous_month_spend else None
        )
        suppliers = (
            OrderItem.objects.filter(order__buyer=request.user, farmer__isnull=False)
            .values(
                "farmer_id",
                "farmer__first_name",
                "farmer__last_name",
                "farmer__email",
                "farmer__profile__farmer_profile__store_name",
            )
            .annotate(orders=Count("order", distinct=True))
            .order_by("-orders")[:4]
        )

        data = {
            "total_orders": orders.count(),
            "monthly_orders": monthly_order_count,
            "previous_month_orders": previous_month_order_count,
            "pending_orders": orders.filter(status="pending").count(),
            "active_deliveries": orders.filter(
                status__in=["confirmed", "processing", "shipped"]
            ).count(),
            "delivered_orders": delivered_orders.count(),
            "total_spent": str(total_spent),
            "monthly_spent": str(current_month_spend),
            "previous_month_spent": str(previous_month_spend),
            "year_spent": str(year_spent),
            "monthly_average": str(monthly_average),
            "monthly_growth_percent": monthly_growth,
            "wishlist_count": wishlist_count,
            "unread_messages": unread_messages,
            "monthly_spend": monthly_spend,
            "category_spend": [
                {"category": category, "total": str(total)}
                for category, total in sorted(
                    categories.items(), key=lambda item: item[1], reverse=True
                )
            ],
            "recent_orders": recent_orders,
            "top_suppliers": [
                {
                    "name": (
                        item["farmer__profile__farmer_profile__store_name"]
                        or " ".join(
                            name for name in (
                                item["farmer__first_name"],
                                item["farmer__last_name"],
                            ) if name
                        )
                        or item["farmer__email"]
                    ),
                    "orders": item["orders"],
                }
                for item in suppliers
            ],
            "notifications": list(notifications[:5].values(
                "id", "title", "body", "link", "created_at", "is_read"
            )),
            "unread_notifications": notifications.filter(is_read=False).count(),
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