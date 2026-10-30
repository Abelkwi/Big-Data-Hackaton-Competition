from django.db.models import Count, Sum
from rest_framework import generics, permissions
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.models import User
from marketplace.models import Product
from orders.models import Order


class HomeStatsView(APIView):
    """Platform statistics for the homepage."""
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        stats = {
            "active_farmers": User.objects.filter(role="farmer", is_active=True).count(),
            "active_buyers": User.objects.filter(role="buyer", is_active=True).count(),
            "products_available": Product.objects.filter(availability_status="available", is_active=True).count(),
            "orders_delivered": Order.objects.filter(status="delivered").count(),
            "ngos_registered": User.objects.filter(role="ngo", is_active=True).count(),
        }
        return Response(stats)


class FeaturedProductsView(APIView):
    """Featured products for homepage."""
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        products = Product.objects.filter(
            is_featured=True,
            availability_status="available",
            is_active=True,
        ).select_related("farmer__profile", "category")[:8]
        
        data = []
        for p in products:
            data.append({
                "id": p.id,
                "name": p.name,
                "slug": p.slug,
                "price": str(p.price_per_unit),
                "unit": p.unit,
                "image": p.main_image.url if p.main_image else None,
                "farmer": p.farmer.email,
                "category": p.category.name if p.category else None,
            })
        return Response(data)
