from django.contrib.auth import get_user_model
from django.db.models import Avg, Sum, Count
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from marketplace.models import Product, Review
from marketplace.serializers import ProductListSerializer
from .models import Profile, FarmerProfile, FarmerFollow, NGOProfile
from .serializers import UserSerializer, FarmerProfileSerializer, NGOProfileSerializer

User = get_user_model()


class FarmerListView(generics.ListAPIView):
    """List all farmers with their profiles."""
    permission_classes = [permissions.AllowAny]
    serializer_class = UserSerializer

    def get_queryset(self):
        return User.objects.filter(role="farmer", is_active=True).select_related("profile")


class FarmerDetailView(APIView):
    """Detailed view of a farmer's store and products."""
    permission_classes = [permissions.AllowAny]

    def get(self, request, slug):
        try:
            farmer_profile = FarmerProfile.objects.select_related("profile__user").get(store_slug=slug)
        except FarmerProfile.DoesNotExist:
            return Response({"detail": "Farmer not found."}, status=status.HTTP_404_NOT_FOUND)

        farmer = farmer_profile.profile.user
        products = Product.objects.filter(
            farmer=farmer, availability_status="available", is_active=True
        ).order_by("-created_at")

        avg_rating = Review.objects.filter(
            product__farmer=farmer, is_approved=True
        ).aggregate(Avg("rating"))["rating__avg"]

        followers_count = FarmerFollow.objects.filter(farmer=farmer).count()
        following_count = FarmerFollow.objects.filter(follower=farmer).count()

        is_following = False
        if request.user.is_authenticated:
            is_following = FarmerFollow.objects.filter(
                follower=request.user, farmer=farmer
            ).exists()

        data = {
            "user": UserSerializer(farmer).data,
            "farmer_profile": FarmerProfileSerializer(farmer_profile).data,
            "products": ProductListSerializer(products, many=True).data,
            "product_count": products.count(),
            "average_rating": round(avg_rating or 0, 1),
            "followers_count": followers_count,
            "following_count": following_count,
            "is_following": is_following,
        }
        return Response(data)


class ToggleFollowView(APIView):
    """Follow or unfollow a farmer."""
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, slug):
        try:
            farmer_profile = FarmerProfile.objects.select_related("profile__user").get(store_slug=slug)
        except FarmerProfile.DoesNotExist:
            return Response({"detail": "Farmer not found."}, status=status.HTTP_404_NOT_FOUND)

        farmer = farmer_profile.profile.user
        if farmer == request.user:
            return Response({"detail": "You cannot follow yourself."}, status=status.HTTP_400_BAD_REQUEST)

        follow, created = FarmerFollow.objects.get_or_create(
            follower=request.user, farmer=farmer
        )
        if not created:
            follow.delete()
            return Response({"detail": "Unfollowed.", "is_following": False})

        return Response({"detail": "Followed.", "is_following": True}, status=status.HTTP_201_CREATED)


class CooperativeListView(generics.ListAPIView):
    """List all NGO/Cooperative profiles."""
    permission_classes = [permissions.AllowAny]
    serializer_class = NGOProfileSerializer

    def get_queryset(self):
        return NGOProfile.objects.filter(is_approved=True)


class CooperativeDetailView(generics.RetrieveAPIView):
    """Detail of a specific NGO/Cooperative."""
    permission_classes = [permissions.AllowAny]
    serializer_class = NGOProfileSerializer
    lookup_field = "slug"
    lookup_url_kwarg = "slug"

    def get_queryset(self):
        return NGOProfile.objects.filter(is_approved=True)
