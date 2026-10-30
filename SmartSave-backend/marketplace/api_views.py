from django.db.models import F, Q
from rest_framework import generics, permissions, status, filters
from rest_framework.response import Response
from rest_framework.views import APIView
from django_filters.rest_framework import DjangoFilterBackend

from .models import Category, Product, Review, Wishlist
from .serializers import (
    CategorySerializer,
    ProductListSerializer,
    ProductDetailSerializer,
    ProductCreateSerializer,
    ReviewSerializer,
    WishlistSerializer,
)


class IsFarmerOrAdmin(permissions.BasePermission):
    """Allow access only to farmers or admin users."""

    def has_permission(self, request, view):
        return request.user.is_authenticated and (
            request.user.role == "farmer" or request.user.is_staff
        )


class IsOwnerOrAdmin(permissions.BasePermission):
    """Object-level permission: only owner or admin can edit."""

    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        return obj.farmer == request.user or request.user.is_staff


# ─── CATEGORIES ───────────────────────────────────────────────


class CategoryListView(generics.ListAPIView):
    """List all active categories with product counts."""
    permission_classes = [permissions.AllowAny]
    serializer_class = CategorySerializer
    queryset = Category.objects.filter(is_active=True)


# ─── PRODUCT LIST / SEARCH ────────────────────────────────────


class ProductListView(generics.ListAPIView):
    """List products with search, filter, sort, and pagination."""
    permission_classes = [permissions.AllowAny]
    serializer_class = ProductListSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = {
        "category": ["exact"],
        "organic": ["exact"],
        "district": ["exact", "icontains"],
        "province": ["exact"],
        "availability_status": ["exact"],
        "price_per_unit": ["gte", "lte"],
    }
    search_fields = ["name", "description", "variety", "district"]
    ordering_fields = ["created_at", "price_per_unit", "name", "views", "average_rating"]
    ordering = ["-created_at"]

    def get_queryset(self):
        return Product.objects.filter(
            availability_status="available",
            verification_status="verified",
            is_active=True,
        ).select_related("farmer", "farmer__profile", "category")


class FeaturedProductListView(generics.ListAPIView):
    """Featured products for homepage."""
    permission_classes = [permissions.AllowAny]
    serializer_class = ProductListSerializer

    def get_queryset(self):
        return Product.objects.filter(
            is_featured=True,
            availability_status="available",
            is_active=True,
        ).select_related("farmer", "farmer__profile", "category")[:12]


class PendingVerificationListView(generics.ListAPIView):
    """List products pending verification (admin only)."""
    permission_classes = [permissions.IsAdminUser]
    serializer_class = ProductListSerializer

    def get_queryset(self):
        return Product.objects.filter(
            verification_status="pending", is_active=True
        ).select_related("farmer", "farmer__profile", "category")


# ─── PRODUCT DETAIL ───────────────────────────────────────────


class ProductDetailView(APIView):
    """Product detail with reviews and related products."""
    permission_classes = [permissions.AllowAny]

    def get(self, request, slug):
        try:
            product = Product.objects.select_related(
                "farmer", "farmer__profile", "category"
            ).prefetch_related("images", "reviews__buyer").get(
                slug=slug, is_active=True
            )
        except Product.DoesNotExist:
            return Response(
                {"detail": "Product not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        # Increment view count
        Product.objects.filter(pk=product.pk).update(views=F("views") + 1)
        product.refresh_from_db()

        reviews = product.reviews.filter(is_approved=True).select_related("buyer")

        related = Product.objects.filter(
            category=product.category,
            is_active=True,
            availability_status="available",
        ).exclude(pk=product.pk)[:8]

        in_wishlist = False
        if request.user.is_authenticated:
            in_wishlist = Wishlist.objects.filter(
                user=request.user, product=product
            ).exists()

        data = ProductDetailSerializer(product).data
        data["reviews"] = ReviewSerializer(reviews, many=True).data
        data["related_products"] = ProductListSerializer(related, many=True).data
        data["in_wishlist"] = in_wishlist

        return Response(data)


# ─── PRODUCT CRUD (Farmer) ────────────────────────────────────


class ProductCreateView(generics.CreateAPIView):
    """Create a new product listing (farmer only)."""
    permission_classes = [IsFarmerOrAdmin]
    serializer_class = ProductCreateSerializer

    def perform_create(self, serializer):
        serializer.save(farmer=self.request.user)


class ProductUpdateView(generics.UpdateAPIView):
    """Update a product listing (owner or admin)."""
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrAdmin]
    serializer_class = ProductCreateSerializer
    lookup_field = "slug"

    def get_queryset(self):
        return Product.objects.filter(is_active=True)


class ProductDeleteView(generics.DestroyAPIView):
    """Delete a product listing (owner or admin)."""
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrAdmin]
    lookup_field = "slug"

    def get_queryset(self):
        return Product.objects.filter(is_active=True)

    def destroy(self, request, *args, **kwargs):
        product = self.get_object()
        product.is_active = False
        product.save()
        return Response(
            {"detail": "Product deactivated successfully."},
            status=status.HTTP_200_OK,
        )


class MyProductListView(generics.ListAPIView):
    """List current farmer's own products."""
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = ProductListSerializer

    def get_queryset(self):
        return Product.objects.filter(
            farmer=self.request.user
        ).select_related("category").order_by("-created_at")


# ─── VERIFICATION WORKFLOW (Admin) ────────────────────────────


class VerifyProductView(APIView):
    """Approve or reject a product (admin only)."""
    permission_classes = [permissions.IsAdminUser]

    def post(self, request, slug):
        try:
            product = Product.objects.get(slug=slug, is_active=True)
        except Product.DoesNotExist:
            return Response(
                {"detail": "Product not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        action = request.data.get("action", "").strip().lower()
        if action == "approve":
            product.verification_status = "verified"
            product.save()
            return Response({"detail": "Product approved.", "status": "verified"})
        elif action == "reject":
            product.verification_status = "rejected"
            product.save()
            return Response({"detail": "Product rejected.", "status": "rejected"})
        return Response(
            {"detail": "Invalid action. Use 'approve' or 'reject'."},
            status=status.HTTP_400_BAD_REQUEST,
        )


# ─── REVIEWS ──────────────────────────────────────────────────


class ReviewCreateView(generics.CreateAPIView):
    """Create or update a review for a product."""
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = ReviewSerializer

    def perform_create(self, serializer):
        product = Product.objects.get(slug=self.kwargs["slug"])
        Review.objects.update_or_create(
            product=product,
            buyer=self.request.user,
            defaults={
                "rating": serializer.validated_data["rating"],
                "comment": serializer.validated_data.get("comment", ""),
            },
        )


# ─── WISHLIST ─────────────────────────────────────────────────


class ToggleWishlistView(APIView):
    """Toggle product in wishlist."""
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, slug):
        try:
            product = Product.objects.get(slug=slug, is_active=True)
        except Product.DoesNotExist:
            return Response(
                {"detail": "Product not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        item, created = Wishlist.objects.get_or_create(
            user=request.user, product=product
        )
        if not created:
            item.delete()
            return Response(
                {"detail": "Removed from wishlist.", "in_wishlist": False}
            )
        return Response(
            {"detail": "Added to wishlist.", "in_wishlist": True},
            status=status.HTTP_201_CREATED,
        )


class WishlistView(generics.ListAPIView):
    """List user's wishlist."""
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = WishlistSerializer

    def get_queryset(self):
        return Wishlist.objects.filter(user=self.request.user).select_related(
            "product", "product__farmer", "product__category"
        )