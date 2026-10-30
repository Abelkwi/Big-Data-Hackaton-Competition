from django.contrib import admin
from django.utils.html import format_html

from .models import Category, Product, ProductImage, Review, Wishlist


class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1
    fields = ("image", "caption", "display_order")


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "display_order", "is_active", "product_count")
    list_filter = ("is_active",)
    search_fields = ("name", "description")
    prepopulated_fields = {"slug": ("name",)}

    def product_count(self, obj):
        return obj.products.count()
    product_count.short_description = "Products"


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "product_thumbnail",
        "name",
        "farmer",
        "category",
        "quantity",
        "unit",
        "price_per_unit",
        "availability_status",
        "verification_status",
        "created_at",
    )
    list_filter = (
        "category",
        "availability_status",
        "verification_status",
        "organic",
        "created_at",
    )
    search_fields = (
        "name",
        "description",
        "farmer__email",
        "farmer__username",
        "district",
    )
    readonly_fields = ("created_at", "updated_at", "views")
    ordering = ("-created_at",)
    inlines = [ProductImageInline]

    def product_thumbnail(self, obj):
        if obj.main_image:
            return format_html(
                '<img src="{}" width="60" height="60" style="object-fit:cover;border-radius:6px;" />',
                obj.main_image.url,
            )
        return "-"
    product_thumbnail.short_description = "Image"

    actions = ["approve_products", "reject_products", "feature_products"]

    def approve_products(self, request, queryset):
        updated = queryset.update(verification_status="verified")
        self.message_user(request, f"{updated} products approved.")
    approve_products.short_description = "Approve selected products"

    def reject_products(self, request, queryset):
        updated = queryset.update(verification_status="rejected")
        self.message_user(request, f"{updated} products rejected.")
    reject_products.short_description = "Reject selected products"

    def feature_products(self, request, queryset):
        updated = queryset.update(is_featured=True)
        self.message_user(request, f"{updated} products marked as featured.")
    feature_products.short_description = "Feature selected products"

@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ("id", "product", "buyer", "rating", "is_approved", "created_at")
    list_filter = ("rating", "is_approved")
    search_fields = ("product__name", "buyer__email", "comment")
    readonly_fields = ("created_at", "updated_at")

    actions = ["approve_reviews"]

    def approve_reviews(self, request, queryset):
        updated = queryset.update(is_approved=True)
        self.message_user(request, f"{updated} reviews approved.")
    approve_reviews.short_description = "Approve selected reviews"


@admin.register(Wishlist)
class WishlistAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "product", "created_at")
    search_fields = ("user__email", "user__username", "product__name")
    list_select_related = ("user", "product")
    readonly_fields = ("created_at",)
    ordering = ("-created_at",)