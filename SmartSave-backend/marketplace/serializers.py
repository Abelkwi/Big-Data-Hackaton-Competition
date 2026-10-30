from rest_framework import serializers

from .models import Category, Product, ProductImage, Review, Wishlist


class CategorySerializer(serializers.ModelSerializer):
    product_count = serializers.SerializerMethodField()

    class Meta:
        model = Category
        fields = [
            "id", "name", "slug", "description", "icon",
            "display_order", "is_active", "product_count",
        ]

    def get_product_count(self, obj):
        return obj.products.filter(is_active=True).count()


class ProductImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductImage
        fields = ["id", "image", "caption", "display_order"]


class ProductListSerializer(serializers.ModelSerializer):
    farmer_name = serializers.SerializerMethodField()
    farmer_store_slug = serializers.SerializerMethodField()
    main_image_url = serializers.SerializerMethodField()
    average_rating = serializers.SerializerMethodField()
    category_name = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = [
            "id", "name", "slug", "category", "category_name",
            "price_per_unit", "unit", "quantity", "main_image_url",
            "farmer_name", "farmer_store_slug", "average_rating",
            "organic", "district", "province", "availability_status",
            "verification_status", "created_at",
        ]

    def get_farmer_name(self, obj):
        return obj.farmer.get_full_name() or obj.farmer.email

    def get_farmer_store_slug(self, obj):
        if hasattr(obj.farmer, "profile") and hasattr(obj.farmer.profile, "farmer_profile"):
            return obj.farmer.profile.farmer_profile.store_slug
        return None

    def get_main_image_url(self, obj):
        if obj.main_image:
            return obj.main_image.url
        return None

    def get_average_rating(self, obj):
        return obj.average_rating

    def get_category_name(self, obj):
        return obj.category.name if obj.category else None


class ProductDetailSerializer(serializers.ModelSerializer):
    images = ProductImageSerializer(many=True, read_only=True)
    farmer_name = serializers.SerializerMethodField()
    farmer_store_slug = serializers.SerializerMethodField()
    farmer_id = serializers.SerializerMethodField()
    average_rating = serializers.SerializerMethodField()
    review_count = serializers.SerializerMethodField()
    category_name = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = [
            "id", "name", "slug", "category", "category_name",
            "variety", "description", "main_image", "images",
            "price_per_unit", "unit", "quantity", "minimum_order",
            "province", "district", "sector", "harvest_date",
            "expiry_date", "organic", "availability_status",
            "verification_status", "farmer_id", "farmer_name",
            "farmer_store_slug", "average_rating", "review_count",
            "views", "created_at", "updated_at",
        ]

    def get_farmer_name(self, obj):
        return obj.farmer.get_full_name() or obj.farmer.email

    def get_farmer_store_slug(self, obj):
        if hasattr(obj.farmer, "profile") and hasattr(obj.farmer.profile, "farmer_profile"):
            return obj.farmer.profile.farmer_profile.store_slug
        return None

    def get_farmer_id(self, obj):
        return obj.farmer.id

    def get_average_rating(self, obj):
        return obj.average_rating

    def get_review_count(self, obj):
        return obj.review_count

    def get_category_name(self, obj):
        return obj.category.name if obj.category else None


class ProductCreateSerializer(serializers.ModelSerializer):
    gallery_images = serializers.ListField(
        child=serializers.ImageField(), write_only=True, required=False
    )

    class Meta:
        model = Product
        fields = [
            "name", "category", "variety", "description",
            "main_image", "gallery_images", "price_per_unit",
            "unit", "quantity", "minimum_order", "province",
            "district", "sector", "harvest_date", "expiry_date",
            "organic", "availability_status",
        ]

    def validate_price_per_unit(self, value):
        if value <= 0:
            raise serializers.ValidationError("Price must be greater than zero.")
        return value

    def validate_quantity(self, value):
        if value <= 0:
            raise serializers.ValidationError("Quantity must be greater than zero.")
        return value

    def create(self, validated_data):
        gallery = validated_data.pop("gallery_images", [])
        product = Product.objects.create(**validated_data)
        for idx, image in enumerate(gallery):
            ProductImage.objects.create(
                product=product, image=image, display_order=idx
            )
        return product


class ReviewSerializer(serializers.ModelSerializer):
    buyer_name = serializers.SerializerMethodField()

    class Meta:
        model = Review
        fields = ["id", "product", "buyer_name", "rating", "comment", "created_at"]
        read_only_fields = ["id", "buyer_name", "created_at"]

    def get_buyer_name(self, obj):
        return obj.buyer.get_full_name() or obj.buyer.email


class WishlistSerializer(serializers.ModelSerializer):
    product = ProductListSerializer(read_only=True)

    class Meta:
        model = Wishlist
        fields = ["id", "product", "created_at"]